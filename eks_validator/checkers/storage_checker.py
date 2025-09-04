"""
Storage validation checker for EKS clusters
"""

from typing import Dict, Any
from loguru import logger


class StorageChecker:
    """Checks storage components including CSI drivers, storage classes, and PVCs"""

    def __init__(self, k8s_client, env_config):
        self.k8s_client = k8s_client
        self.env_config = env_config

    def check_all(self) -> Dict[str, Any]:
        """Run all storage checks"""
        if not self.k8s_client:
            return {
                "check_status": "FAIL",
                "message": "Kubernetes client not available for storage checks",
            }

        return {
            "csi_drivers": self.check_csi_drivers(),
            "storage_classes": self.check_storage_classes(),
            "persistent_volumes": self.check_persistent_volumes(),
            "persistent_volume_claims": self.check_persistent_volume_claims(),
        }

    def check_csi_drivers(self) -> Dict[str, Any]:
        """Check CSI driver installation and status"""
        try:
            # Check for EBS CSI driver
            ebs_csi_result = self._check_csi_driver("ebs.csi.aws.com")

            # Check for EFS CSI driver
            efs_csi_result = self._check_csi_driver("efs.csi.aws.com")

            results = {
                "ebs_csi_driver": ebs_csi_result,
                "efs_csi_driver": efs_csi_result,
            }

            # Overall assessment
            ebs_healthy = ebs_csi_result.get("check_status") == "PASS"
            efs_healthy = efs_csi_result.get("check_status") == "PASS"

            if ebs_healthy:
                results["overall_status"] = "PASS"
                results["message"] = "EBS CSI driver is properly installed"
            elif efs_healthy:
                results["overall_status"] = "WARN"
                results["message"] = "Only EFS CSI driver found, EBS CSI driver missing"
            else:
                results["overall_status"] = "FAIL"
                results["message"] = "No CSI drivers found"

            return results

        except Exception as e:
            logger.error(f"Failed to check CSI drivers: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CSI drivers: {e}",
                "error": str(e),
            }

    def _check_csi_driver(self, driver_name: str) -> Dict[str, Any]:
        """Check if a specific CSI driver is installed"""
        try:
            # For EKS add-on installations, use different naming patterns
            if driver_name == "ebs.csi.aws.com":
                # EKS add-on naming pattern
                deployment_names = ["ebs-csi-controller"]
                daemonset_names = ["ebs-csi-node"]
                # Also check traditional self-managed pattern
                deployment_names.append("csi-ebs-controller")
                daemonset_names.append("csi-ebs-node")
            elif driver_name == "efs.csi.aws.com":
                # EKS add-on naming pattern
                deployment_names = ["efs-csi-controller"]
                daemonset_names = ["efs-csi-node"]
                # Also check traditional self-managed pattern
                deployment_names.append("csi-efs-controller")
                daemonset_names.append("csi-efs-node")
            else:
                # Generic pattern for other CSI drivers
                driver_prefix = driver_name.split(".")[0]
                deployment_names = [f"csi-{driver_prefix}-controller"]
                daemonset_names = [f"csi-{driver_prefix}-node"]

            # Check deployments (at least one must exist)
            deployment_found = False
            deployment_result = None
            for dep_name in deployment_names:
                dep_result = self._check_deployment(dep_name, "kube-system")
                if dep_result.get("check_status") == "PASS":
                    deployment_found = True
                    deployment_result = dep_result
                    break
                elif dep_result.get("check_status") in ["WARN", "PASS"]:
                    deployment_result = dep_result

            # Check daemonsets (at least one must exist)
            daemonset_found = False
            daemonset_result = None
            for ds_name in daemonset_names:
                ds_result = self._check_daemonset(ds_name, "kube-system")
                if ds_result.get("check_status") == "PASS":
                    daemonset_found = True
                    daemonset_result = ds_result
                    break
                elif ds_result.get("check_status") in ["WARN", "PASS"]:
                    daemonset_result = ds_result

            # Check for StorageClass
            storage_class_result = self._check_storage_class_for_driver(driver_name)

            result = {
                "deployment": deployment_result,
                "daemonset": daemonset_result,
                "storage_class": storage_class_result,
            }

            # Determine overall status - require at least deployment OR
            # daemonset to be healthy
            components_healthy = (
                deployment_found or daemonset_found
            ) and storage_class_result.get("check_status") == "PASS"

            if components_healthy:
                result["check_status"] = "PASS"
                result["message"] = f"CSI driver {driver_name} is fully operational"
            elif deployment_found or daemonset_found:
                result["check_status"] = "WARN"
                result["message"] = (
                    f"CSI driver {driver_name} is partially installed "
                    "(missing storage class)"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"CSI driver {driver_name} is not installed"

            return result

        except Exception as e:
            logger.error(f"Failed to check CSI driver {driver_name}: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CSI driver {driver_name}: {e}",
                "error": str(e),
            }

    def _check_deployment(self, name: str, namespace: str) -> Dict[str, Any]:
        """Check if a deployment exists and is healthy"""
        try:
            from kubernetes.client import AppsV1Api

            apps_v1 = AppsV1Api()
            deployment = apps_v1.read_namespaced_deployment(name, namespace)

            ready_replicas = deployment.status.ready_replicas or 0
            desired_replicas = deployment.spec.replicas or 0

            result = {
                "name": name,
                "namespace": namespace,
                "ready_replicas": ready_replicas,
                "desired_replicas": desired_replicas,
                "available_replicas": deployment.status.available_replicas or 0,
            }

            if ready_replicas == desired_replicas and desired_replicas > 0:
                result["check_status"] = "PASS"
                result["message"] = (
                    "Deployment "
                    + name
                    + " is healthy ("
                    + str(ready_replicas)
                    + "/"
                    + str(desired_replicas)
                    + " ready)"
                )
            elif ready_replicas > 0:
                result["check_status"] = "WARN"
                result["message"] = (
                    f"Deployment {name} is partially ready "
                    f"({ready_replicas}/{desired_replicas})"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"Deployment {name} has no ready replicas"

            return result

        except Exception as e:
            if hasattr(e, "status") and e.status == 404:
                return {
                    "check_status": "FAIL",
                    "message": f"Deployment {name} not found in namespace {namespace}",
                }
            else:
                return {
                    "check_status": "FAIL",
                    "message": f"Failed to check deployment {name}: {e}",
                    "error": str(e),
                }
        except Exception as e:
            return {
                "check_status": "FAIL",
                "message": f"Failed to check deployment {name}: {e}",
            }

    def _check_daemonset(self, name: str, namespace: str) -> Dict[str, Any]:
        """Check if a daemonset exists and is healthy"""
        try:
            from kubernetes.client import AppsV1Api

            apps_v1 = AppsV1Api()
            daemonset = apps_v1.read_namespaced_daemon_set(name, namespace)

            desired_number = daemonset.status.desired_number_scheduled or 0
            ready_number = daemonset.status.number_ready or 0

            result = {
                "name": name,
                "namespace": namespace,
                "desired_number": desired_number,
                "ready_number": ready_number,
                "available_number": daemonset.status.number_available or 0,
            }

            if ready_number == desired_number and desired_number > 0:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"DaemonSet {name} is healthy "
                    f"({ready_number}/{desired_number} ready)"
                )
            elif ready_number > 0:
                result["check_status"] = "WARN"
                result["message"] = (
                    f"DaemonSet {name} is partially ready "
                    f"({ready_number}/{desired_number})"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"DaemonSet {name} has no ready pods"

            return result

        except Exception as e:
            if hasattr(e, "status") and e.status == 404:
                return {
                    "check_status": "FAIL",
                    "message": f"DaemonSet {name} not found in namespace {namespace}",
                }
            else:
                return {
                    "check_status": "FAIL",
                    "message": f"Failed to check daemonset {name}: {e}",
                }
        except Exception as e:
            return {
                "check_status": "FAIL",
                "message": f"Failed to check daemonset {name}: {e}",
            }

    def _check_storage_class_for_driver(self, driver_name: str) -> Dict[str, Any]:
        """Check if storage class exists for a CSI driver"""
        try:
            from kubernetes.client import StorageV1Api

            storage_api = StorageV1Api()
            storage_classes = storage_api.list_storage_class()

            driver_prefix = driver_name.split(".")[
                0
            ]  # e.g., 'ebs' from 'ebs.csi.aws.com'

            for sc in storage_classes.items:
                provisioner = sc.provisioner
                if driver_name in provisioner or driver_prefix in provisioner:
                    return {
                        "check_status": "PASS",
                        "message": (
                            f"StorageClass {sc.metadata.name} found for {driver_name}"
                        ),
                        "storage_class_name": sc.metadata.name,
                        "provisioner": provisioner,
                        "reclaim_policy": sc.reclaim_policy,
                        "volume_binding_mode": sc.volume_binding_mode,
                    }

            return {
                "check_status": "FAIL",
                "message": f"No StorageClass found for {driver_name}",
            }

        except Exception as e:
            return {
                "check_status": "FAIL",
                "message": f"Failed to check storage classes: {e}",
            }

    def check_storage_classes(self) -> Dict[str, Any]:
        """Check all storage classes in the cluster"""
        try:
            from kubernetes.client import StorageV1Api

            storage_api = StorageV1Api()
            storage_classes = storage_api.list_storage_class()

            results = {}
            for sc in storage_classes.items:
                sc_name = sc.metadata.name
                results[sc_name] = {
                    "provisioner": sc.provisioner,
                    "reclaim_policy": sc.reclaim_policy,
                    "volume_binding_mode": sc.volume_binding_mode,
                    "allow_volume_expansion": sc.allow_volume_expansion or False,
                    "parameters": sc.parameters or {},
                }

                # Basic validation
                if sc.provisioner and sc.reclaim_policy:
                    results[sc_name]["check_status"] = "PASS"
                    results[sc_name][
                        "message"
                    ] = f"StorageClass {sc_name} is properly configured"
                else:
                    results[sc_name]["check_status"] = "WARN"
                    results[sc_name][
                        "message"
                    ] = f"StorageClass {sc_name} has incomplete configuration"

            if not results:
                return {
                    "check_status": "WARN",
                    "message": "No storage classes found in cluster",
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check storage classes: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check storage classes: {e}",
                "error": str(e),
            }

    def check_persistent_volumes(self) -> Dict[str, Any]:
        """Check persistent volumes in the cluster"""
        try:
            pv_list = self.k8s_client.list_persistent_volume()

            results = {}
            for pv in pv_list.items:
                pv_name = pv.metadata.name
                results[pv_name] = {
                    "phase": pv.status.phase,
                    "capacity": (
                        pv.spec.capacity.get("storage", "N/A")
                        if pv.spec.capacity
                        else "N/A"
                    ),
                    "access_modes": pv.spec.access_modes,
                    "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
                    "storage_class": pv.spec.storage_class_name,
                    "volume_mode": pv.spec.volume_mode,
                }

                # Determine status
                if pv.status.phase == "Bound":
                    results[pv_name]["check_status"] = "PASS"
                    results[pv_name]["message"] = f"PV {pv_name} is bound and available"
                elif pv.status.phase == "Available":
                    results[pv_name]["check_status"] = "PASS"
                    results[pv_name]["message"] = f"PV {pv_name} is available"
                elif pv.status.phase == "Pending":
                    results[pv_name]["check_status"] = "WARN"
                    results[pv_name]["message"] = f"PV {pv_name} is pending"
                else:
                    results[pv_name]["check_status"] = "FAIL"
                    results[pv_name][
                        "message"
                    ] = f"PV {pv_name} phase: {pv.status.phase}"

            if not results:
                return {
                    "check_status": "INFO",
                    "message": "No persistent volumes found in cluster",
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check persistent volumes: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check persistent volumes: {e}",
                "error": str(e),
            }

    def check_persistent_volume_claims(self) -> Dict[str, Any]:
        """Check persistent volume claims across all namespaces"""
        try:
            pvc_list = self.k8s_client.list_persistent_volume_claim_for_all_namespaces()

            results = {}
            for pvc in pvc_list.items:
                pvc_name = pvc.metadata.name
                namespace = pvc.metadata.namespace

                key = f"{namespace}/{pvc_name}"
                results[key] = {
                    "namespace": namespace,
                    "name": pvc_name,
                    "phase": pvc.status.phase,
                    "capacity": (
                        pvc.status.capacity.get("storage", "N/A")
                        if pvc.status.capacity
                        else "N/A"
                    ),
                    "requested_storage": (
                        pvc.spec.resources.requests.get("storage", "N/A")
                        if pvc.spec.resources and pvc.spec.resources.requests
                        else "N/A"
                    ),
                    "access_modes": pvc.spec.access_modes,
                    "storage_class": pvc.spec.storage_class_name,
                    "volume_name": pvc.spec.volume_name,
                }

                # Determine status
                if pvc.status.phase == "Bound":
                    results[key]["check_status"] = "PASS"
                    results[key]["message"] = f"PVC {key} is bound"
                elif pvc.status.phase == "Pending":
                    results[key]["check_status"] = "WARN"
                    results[key]["message"] = f"PVC {key} is pending"
                else:
                    results[key]["check_status"] = "FAIL"
                    results[key]["message"] = f"PVC {key} phase: {pvc.status.phase}"

            if not results:
                return {
                    "check_status": "INFO",
                    "message": "No persistent volume claims found in cluster",
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check persistent volume claims: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check persistent volume claims: {e}",
                "error": str(e),
            }
