"""Deterministic validator for cloud containment grammar and honest-data rules."""
import re
from typing import Any, Dict, List
from app.models.schemas import DiagramContent, DiagramType, ValidationIssue, ValidationReport


class DiagramValidator:
    """Validates structural containment, honest data encodings, and editorial skin rules."""

    @classmethod
    def validate(cls, diagram_type: DiagramType, content: DiagramContent, svg_code: str = "") -> ValidationReport:
        issues: List[ValidationIssue] = []
        passed_rules: List[str] = []
        data = content.data or {}

        # 1. Skin & Aesthetic linting
        skin_ok = cls._lint_skin(svg_code, issues, passed_rules)

        # 2. Containment validation
        containment_ok = True
        if diagram_type in {"architecture_azure", "architecture_aws"}:
            containment_ok = cls._validate_cloud_containment(data, issues, passed_rules)

        # 3. Honest data validation
        honest_ok = cls._validate_honest_data(diagram_type, data, issues, passed_rules)

        # Overall validity
        has_errors = any(i.severity == "error" for i in issues)
        valid = (not has_errors) and skin_ok and containment_ok and honest_ok

        return ValidationReport(
            valid=valid,
            diagram_type=diagram_type,
            total_checks=len(passed_rules) + len(issues),
            issues=issues,
            passed_rules=passed_rules,
            honest_data_compliant=honest_ok,
            containment_compliant=containment_ok,
            skin_compliant=skin_ok,
        )

    @classmethod
    def _lint_skin(cls, svg_code: str, issues: List[ValidationIssue], passed_rules: List[str]) -> bool:
        if not svg_code:
            passed_rules.append("skin.omitted_check")
            return True

        clean = True

        # Rule: No drop-shadow filters
        if re.search(r"feDropShadow|feGaussianBlur|filter=[\"']url\(#", svg_code, re.I):
            issues.append(
                ValidationIssue(
                    rule="skin.no_drop_shadows",
                    severity="error",
                    message="Editorial rule violation: drop shadows and blur filters are strictly forbidden.",
                )
            )
            clean = False
        else:
            passed_rules.append("skin.no_drop_shadows")

        # Rule: No rainbow gradients
        if re.search(r"<radialGradient|<linearGradient", svg_code, re.I):
            issues.append(
                ValidationIssue(
                    rule="skin.no_rainbow_gradients",
                    severity="warning",
                    message="Multi-stop gradients should be avoided in favor of crisp ink-opacity ramps.",
                )
            )
        else:
            passed_rules.append("skin.no_rainbow_gradients")

        # Rule: ViewBox responsiveness
        if "viewBox=" in svg_code:
            passed_rules.append("skin.responsive_viewbox")
        else:
            issues.append(
                ValidationIssue(
                    rule="skin.responsive_viewbox",
                    severity="error",
                    message="SVG root must declare a responsive viewBox attribute.",
                )
            )
            clean = False

        return clean

    @classmethod
    def _validate_cloud_containment(
        cls, data: Dict[str, Any], issues: List[ValidationIssue], passed_rules: List[str]
    ) -> bool:
        valid = True

        # Support both legacy single VNet and new multi-VNet format
        vnet_list = data.get("vnets", [])
        if not vnet_list:
            # Legacy format
            vnet_list = [{
                "name": data.get("vnet", "VNet"),
                "subnets": data.get("subnets", []),
                "paas_services": data.get("paas_services", []),
            }]

        # Hierarchy presence
        has_sub = bool(data.get("subscription"))
        has_rg = bool(data.get("resource_group"))
        has_vnet = len(vnet_list) > 0

        if has_sub and has_rg and has_vnet:
            passed_rules.append("containment.cloud_hierarchy_4level")
        else:
            issues.append(
                ValidationIssue(
                    rule="containment.cloud_hierarchy_4level",
                    severity="error",
                    message="Cloud architecture topology must clearly model subscription, resource group, and virtual network boundaries.",
                )
            )
            valid = False

        # Collect all private endpoint IDs across all VNets for cross-VNet reference validation
        all_pe_ids = set()
        for vnet in vnet_list:
            for snet in vnet.get("subnets", []):
                for n in snet.get("nodes", []):
                    if n.get("type") == "private_endpoint" and "id" in n:
                        all_pe_ids.add(n["id"])

        # Validate each VNet
        for vnet in vnet_list:
            subnets = vnet.get("subnets", [])
            vnet_paas = vnet.get("paas_services", [])

            # Azure Case Study Rule: A PaaS service is NEVER inside a subnet.
            # It must sit in the resource group; only its private endpoint sits in the subnet.
            for snet in subnets:
                nodes = snet.get("nodes", [])
                for n in nodes:
                    node_type = str(n.get("type", "")).lower()
                    node_label = str(n.get("label", "")).lower()
                    if "paas" in node_type or "sql database" in node_label or "storage account" in node_label:
                        issues.append(
                            ValidationIssue(
                                rule="containment.paas_isolation",
                                severity="error",
                                message=f"PaaS violation in VNet '{vnet.get('name')}' subnet '{snet.get('name')}': '{n.get('label')}' cannot be placed directly inside a subnet. Only its private endpoint belongs inside a subnet.",
                                element_id=n.get("id"),
                            )
                        )
                        valid = False

            # Private Endpoint Linkage Rule:
            # Every PaaS service must target an existing private endpoint in a subnet (can be in any VNet)
            for ps in vnet_paas:
                target_pe = ps.get("target_pe")
                if target_pe and target_pe not in all_pe_ids:
                    issues.append(
                        ValidationIssue(
                            rule="containment.private_endpoint_linkage",
                            severity="error",
                            message=f"PaaS service '{ps.get('label')}' in VNet '{vnet.get('name')}' references non-existent private endpoint target '{target_pe}'.",
                            element_id=ps.get("id"),
                        )
                    )
                    valid = False

        if "containment.paas_isolation" not in [i.rule for i in issues]:
            passed_rules.append("containment.paas_isolation")

        if "containment.private_endpoint_linkage" not in [i.rule for i in issues]:
            passed_rules.append("containment.private_endpoint_linkage")

        # Peering validation
        peerings = data.get("peerings", [])
        vnet_names = {v.get("name") for v in vnet_list}
        for peering in peerings:
            src = peering.get("source_vnet")
            dst = peering.get("target_vnet")
            if src not in vnet_names:
                issues.append(
                    ValidationIssue(
                        rule="containment.peering_invalid_source",
                        severity="error",
                        message=f"Peering references non-existent source VNet '{src}'.",
                        element_id=f"peering-{src}-{dst}",
                    )
                )
                valid = False
            if dst not in vnet_names:
                issues.append(
                    ValidationIssue(
                        rule="containment.peering_invalid_target",
                        severity="error",
                        message=f"Peering references non-existent target VNet '{dst}'.",
                        element_id=f"peering-{src}-{dst}",
                    )
                )
                valid = False
            if src == dst:
                issues.append(
                    ValidationIssue(
                        rule="containment.peering_self_reference",
                        severity="error",
                        message="Peering cannot reference the same VNet as both source and target.",
                        element_id=f"peering-{src}-{dst}",
                    )
                )
                valid = False
        peering_errors = {"containment.peering_invalid_source", "containment.peering_invalid_target", "containment.peering_self_reference"}
        if peerings and not any(i.rule in peering_errors for i in issues):
            passed_rules.append("containment.peering_valid")

        # NSG Flow Rules Validation
        nsg_rules = data.get("nsg_rules", {})
        # nsg_rules is a dict: subnet_ref -> list of rules
        # Each rule: {name, priority, direction, access, protocol, source_port_range, destination_port_range, source_address_prefix, destination_address_prefix}
        all_subnet_refs = set()
        for vnet in vnet_list:
            for snet in vnet.get("subnets", []):
                vnet_name = vnet.get("name", "")
                snet_name = snet.get("name", "")
                if vnet_name and snet_name:
                    all_subnet_refs.add(f"{vnet_name}/{snet_name}")

        for subnet_ref, rules in nsg_rules.items():
            if subnet_ref not in all_subnet_refs:
                issues.append(
                    ValidationIssue(
                        rule="containment.nsg_invalid_subnet_reference",
                        severity="error",
                        message=f"NSG rules reference non-existent subnet '{subnet_ref}'.",
                        element_id=f"nsg-{subnet_ref}",
                    )
                )
                valid = False
                continue

            for rule in rules:
                # Validate required fields
                required_fields = ["name", "priority", "direction", "access", "protocol"]
                for field in required_fields:
                    if field not in rule:
                        issues.append(
                            ValidationIssue(
                                rule="containment.nsg_missing_field",
                                severity="error",
                                message=f"NSG rule '{rule.get('name', 'unknown')}' in subnet '{subnet_ref}' is missing required field: {field}.",
                                element_id=f"nsg-{subnet_ref}-{rule.get('name', 'unknown')}",
                            )
                        )
                        valid = False

                # Validate priority range (100-4096)
                priority = rule.get("priority", 0)
                if not (100 <= priority <= 4096):
                    issues.append(
                        ValidationIssue(
                            rule="containment.nsg_invalid_priority",
                            severity="error",
                            message=f"NSG rule '{rule.get('name')}' in subnet '{subnet_ref}' has invalid priority {priority}. Must be 100-4096.",
                            element_id=f"nsg-{subnet_ref}-{rule.get('name')}",
                        )
                    )
                    valid = False

                # Validate direction
                if rule.get("direction") not in ("Inbound", "Outbound"):
                    issues.append(
                        ValidationIssue(
                            rule="containment.nsg_invalid_direction",
                            severity="error",
                            message=f"NSG rule '{rule.get('name')}' in subnet '{subnet_ref}' has invalid direction. Must be 'Inbound' or 'Outbound'.",
                            element_id=f"nsg-{subnet_ref}-{rule.get('name')}",
                        )
                    )
                    valid = False

                # Validate access
                if rule.get("access") not in ("Allow", "Deny"):
                    issues.append(
                        ValidationIssue(
                            rule="containment.nsg_invalid_access",
                            severity="error",
                            message=f"NSG rule '{rule.get('name')}' in subnet '{subnet_ref}' has invalid access. Must be 'Allow' or 'Deny'.",
                            element_id=f"nsg-{subnet_ref}-{rule.get('name')}",
                        )
                    )
                    valid = False

                # Validate protocol
                if rule.get("protocol") not in ("Tcp", "Udp", "Icmp", "*"):
                    issues.append(
                        ValidationIssue(
                            rule="containment.nsg_invalid_protocol",
                            severity="error",
                            message=f"NSG rule '{rule.get('name')}' in subnet '{subnet_ref}' has invalid protocol. Must be 'Tcp', 'Udp', 'Icmp', or '*'.",
                            element_id=f"nsg-{subnet_ref}-{rule.get('name')}",
                        )
                    )
                    valid = False

        if nsg_rules and "containment.nsg_invalid_subnet_reference" not in [i.rule for i in issues]:
            passed_rules.append("containment.nsg_rules_valid")

        # Route Table Validation
        route_tables = data.get("route_tables", {})
        # route_tables is a dict: subnet_ref -> list of routes
        # Each route: {name, address_prefix, next_hop_type, next_hop_ip (optional)}

        for subnet_ref, routes in route_tables.items():
            if subnet_ref not in all_subnet_refs:
                issues.append(
                    ValidationIssue(
                        rule="containment.route_table_invalid_subnet_reference",
                        severity="error",
                        message=f"Route table references non-existent subnet '{subnet_ref}'.",
                        element_id=f"rt-{subnet_ref}",
                    )
                )
                valid = False
                continue

            has_default_route = False
            for route in routes:
                required_fields = ["name", "address_prefix", "next_hop_type"]
                for field in required_fields:
                    if field not in route:
                        issues.append(
                            ValidationIssue(
                                rule="containment.route_table_missing_field",
                                severity="error",
                                message=f"Route '{route.get('name', 'unknown')}' in subnet '{subnet_ref}' is missing required field: {field}.",
                                element_id=f"rt-{subnet_ref}-{route.get('name', 'unknown')}",
                            )
                        )
                        valid = False

                if route.get("address_prefix") == "0.0.0.0/0":
                    has_default_route = True
                    if route.get("next_hop_type") not in ("Internet", "VirtualAppliance", "VirtualNetworkGateway", "VnetLocal", "None"):
                        issues.append(
                            ValidationIssue(
                                rule="containment.route_table_invalid_default_next_hop",
                                severity="error",
                                message=f"Default route (0.0.0.0/0) in subnet '{subnet_ref}' has invalid next_hop_type '{route.get('next_hop_type')}'.",
                                element_id=f"rt-{subnet_ref}-{route.get('name')}",
                            )
                        )
                        valid = False

                valid_next_hop_types = ("VirtualAppliance", "VirtualNetworkGateway", "VnetLocal", "Internet", "None")
                if route.get("next_hop_type") not in valid_next_hop_types:
                    issues.append(
                        ValidationIssue(
                            rule="containment.route_table_invalid_next_hop_type",
                            severity="error",
                            message=f"Route '{route.get('name')}' in subnet '{subnet_ref}' has invalid next_hop_type '{route.get('next_hop_type')}'.",
                            element_id=f"rt-{subnet_ref}-{route.get('name')}",
                        )
                    )
                    valid = False

            # Warn if no default route (0.0.0.0/0) to Internet or VirtualAppliance
            if routes and not has_default_route:
                issues.append(
                    ValidationIssue(
                        rule="containment.route_table_missing_default_route",
                        severity="warning",
                        message=f"Route table for subnet '{subnet_ref}' has no default route (0.0.0.0/0) to Internet or VirtualAppliance.",
                        element_id=f"rt-{subnet_ref}",
                    )
                )

        if route_tables and "containment.route_table_invalid_subnet_reference" not in [i.rule for i in issues]:
            passed_rules.append("containment.route_tables_valid")

        return valid

    @classmethod
    def _validate_honest_data(
        cls, diagram_type: DiagramType, data: Dict[str, Any], issues: List[ValidationIssue], passed_rules: List[str]
    ) -> bool:
        valid = True

        if diagram_type == "treemap":
            items = data.get("items", [])
            if not items:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.treemap_non_empty",
                        severity="error",
                        message="Treemap requires at least one data item with positive numeric value.",
                    )
                )
                return False

            has_negative = any(i.get("value", 0) <= 0 for i in items)
            if has_negative:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.treemap_positive_values",
                        severity="error",
                        message="Honest-data rule: treemap area is the only encoding and all values must be strictly positive.",
                    )
                )
                valid = False
            else:
                passed_rules.append("honest_data.treemap_positive_values")

        elif diagram_type == "sankey":
            left_nodes = data.get("left_nodes", [])
            right_nodes = data.get("right_nodes", [])
            if not left_nodes or not right_nodes:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.sankey_bipartite",
                        severity="error",
                        message="Sankey requires both source (left) and target (right) nodes.",
                    )
                )
                return False

            sum_in = sum(n.get("value", 0) for n in left_nodes)
            sum_out = sum(n.get("value", 0) for n in right_nodes)
            # Tolerance 15% or explicit loss node
            loss_declared = any("loss" in n.get("id", "").lower() or "dissipation" in n.get("label", "").lower() for n in right_nodes)
            if abs(sum_in - sum_out) > 0.01 and not loss_declared:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.sankey_conservation_of_mass",
                        severity="warning",
                        message=f"Sankey flow conservation warning: inputs sum to {sum_in} but outputs sum to {sum_out}. Declare a dissipation/loss node or balance flows.",
                    )
                )
            else:
                passed_rules.append("honest_data.sankey_conservation_of_mass")

        elif diagram_type == "slopegraph":
            items = data.get("items", [])
            if not items:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.slopegraph_items",
                        severity="error",
                        message="Slopegraph requires at least one item comparing moment A to moment B.",
                    )
                )
                return False
            passed_rules.append("honest_data.slopegraph_items")

        elif diagram_type == "waffle":
            categories = data.get("categories", [])
            if not categories:
                issues.append(
                    ValidationIssue(
                        rule="honest_data.waffle_categories",
                        severity="error",
                        message="Waffle chart requires categorical count entries.",
                    )
                )
                return False
            passed_rules.append("honest_data.waffle_categories")

        elif diagram_type == "sbgn_pd":
            has_species = bool(data.get("macromolecules") or data.get("complexes"))
            if has_species:
                passed_rules.append("sbgn.species_declared")
            else:
                issues.append(
                    ValidationIssue(
                        rule="sbgn.species_declared",
                        severity="error",
                        message="SBGN Process Description requires at least one macromolecule or complex entity.",
                    )
                )
                valid = False

        return valid
