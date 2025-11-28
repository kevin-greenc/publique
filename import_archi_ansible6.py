import os
import xml.etree.ElementTree as ET
import yaml

BASE_DIR = "ansible-project"
NS = {"archi": "http://www.opengroup.org/xsd/archimate/3.0/"}
XSI_TYPE_ATTR = "{http://www.w3.org/2001/XMLSchema-instance}type"

# Mapping ApplicationComponent -> apt install
APT_MAPPING = {
    "Apache2": "apache2",
    "MariaDB": "mariadb-server",
}

def create_base_structure():
    for folder in ["inventories", "playbooks", "roles"]:
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

    inv_path = os.path.join(BASE_DIR, "inventories", "hosts.yml")
    if not os.path.exists(inv_path):
        with open(inv_path, "w") as f:
            f.write("all:\n  children:\n")

    playbook_path = os.path.join(BASE_DIR, "playbooks", "site.yml")
    if not os.path.exists(playbook_path):
        with open(playbook_path, "w") as f:
            f.write("# Playbook principal généré automatiquement\n")

def create_role(role_name):
    role_dir = role_name.lower()
    role_path = os.path.join(BASE_DIR, "roles", role_dir)
    os.makedirs(os.path.join(role_path, "tasks"), exist_ok=True)
    os.makedirs(os.path.join(role_path, "handlers"), exist_ok=True)
    os.makedirs(os.path.join(role_path, "vars"), exist_ok=True)
    os.makedirs(os.path.join(role_path, "templates"), exist_ok=True)

    tasks_file = os.path.join(role_path, "tasks", "main.yml")
    if not os.path.exists(tasks_file):
        with open(tasks_file, "w") as f:
            f.write(f"# Tasks pour le rôle {role_name}\n")
            f.write("---\n")

    for sub in ["handlers", "vars"]:
        main_file = os.path.join(role_path, sub, "main.yml")
        if not os.path.exists(main_file):
            with open(main_file, "w") as f:
                f.write(f"# {sub.capitalize()} pour le rôle {role_name}\n")

    return role_path

def add_group_and_play(node_name, service_roles):
    group = f"{node_name.lower()}s"
    host = node_name.lower()

    # Inventaire
    inv_path = os.path.join(BASE_DIR, "inventories", "hosts.yml")
    with open(inv_path, "a") as f:
        f.write(f"    {group}:\n")
        f.write("      hosts:\n")
        f.write(f"        {host}:\n")

    # Playbook principal
    playbook_path = os.path.join(BASE_DIR, "playbooks", "site.yml")
    with open(playbook_path, "a") as f:
        f.write(f"- name: Déploiement {node_name}\n")
        f.write(f"  hosts: {group}\n")
        f.write("  become: true\n")
        f.write("  roles:\n")
        for role in service_roles:
            f.write(f"    - {role.lower()}\n")
        f.write("\n")

def add_component_task(component_name, role_path):
    pkg = APT_MAPPING.get(component_name)
    if pkg:
        tasks_file = os.path.join(role_path, "tasks", "main.yml")
        task = {
            "name": f"Installer {component_name}",
            "ansible.builtin.apt": {
                "name": pkg,
                "state": "present",
                "update_cache": True,
            },
        }
        with open(tasks_file, "a") as f:
            f.write(yaml.dump([task], allow_unicode=True))

def generate_from_archimate(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    elements = {}
    for elem in root.findall(".//archi:element", NS):
        elem_id = elem.get("identifier")
        elem_type = elem.get(XSI_TYPE_ATTR)
        name_tag = elem.find("archi:name", NS)
        name = name_tag.text if name_tag is not None else None
        elements[elem_id] = {"type": elem_type, "name": name}

    # Relations Realization
    realizations = []
    for rel in root.findall(".//archi:relationship", NS):
        if rel.get(XSI_TYPE_ATTR) == "Realization":
            realizations.append((rel.get("source"), rel.get("target")))

    # Associer Node -> Service, Service -> Component
    node_services = {}
    service_components = {}

    for src, tgt in realizations:
        src_type = elements.get(src, {}).get("type")
        tgt_type = elements.get(tgt, {}).get("type")

        if src_type == "Node" and tgt_type == "ApplicationService":
            node_services.setdefault(src, []).append(tgt)

        if src_type == "ApplicationComponent" and tgt_type == "ApplicationService":
            service_components.setdefault(tgt, []).append(src)

    # Générer inventaire et rôles
    for node_id, services in node_services.items():
        node_name = elements[node_id]["name"]
        service_roles = []
        for svc_id in services:
            svc_name = elements[svc_id]["name"]
            service_roles.append(svc_name)
            role_path = create_role(svc_name)

            # Ajouter composants liés
            for comp_id in service_components.get(svc_id, []):
                comp_name = elements[comp_id]["name"]
                add_component_task(comp_name, role_path)

        # Node → uniquement inventaire + play qui appelle les rôles de service
        add_group_and_play(node_name, service_roles)

if __name__ == "__main__":
    create_base_structure()
    generate_from_archimate("archimate_model.xml")
