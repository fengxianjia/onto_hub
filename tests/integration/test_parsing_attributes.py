import pytest
import time
import zipfile
import json

@pytest.fixture
def attribute_zip(tmp_path):
    """Creates a zip file with markdown content for attribute parsing."""
    p = tmp_path / "attribute_test.zip"
    
    md_content = """---
type: Project
---
# Project Alpha

Status: Active
Priority: High
Owner: John Doe
"""

    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Project Alpha.md", md_content)
        
    return str(p)

def test_parsing_attributes(client, unique_code, attribute_zip):
    print(f"Testing attribute parsing for {unique_code}")
    
    # 1. Create Parsing Template with Attribute Rules
    rules = {
        "entity": {
            "name_source": "filename_no_ext",
            "category_source": "frontmatter:type"
        },
        "attribute": {
            "regex_patterns": [
                {"key": "status", "pattern": r"Status: (\w+)"},
                {"key": "priority", "pattern": r"Priority: (\w+)"}
            ]
        }
    }
    
    template_name = f"Template-Attr-{unique_code}"
    template = client.create_template(name=template_name, rules=rules)
    template_id = template['id']
    print(f"Created template {template_id}")
    
    # 2. Create Ontology with Template
    v1 = client.create_ontology(attribute_zip, code=unique_code, name="Attribute Test", template_id=template_id)
    v1_id = v1['id']
    print(f"Created ontology {v1_id}")
    
    # 3. Wait for Parsing
    print("Waiting for parsing...")
    nodes = []
    for i in range(10):
        time.sleep(2)
        graph = client.get_ontology_graph(v1_id)
        nodes = graph.get("nodes", [])
        if len(nodes) >= 1:
            break
            
    # 4. Assertions
    assert len(nodes) == 1, "Should have 1 node"
    node = nodes[0]
    print(f"Node Metadata: {node['metadata_json']}")
    
    metadata = json.loads(node['metadata_json'])
    
    # Check Frontmatter
    assert metadata.get("type") == "Project"
    
    # Check Regex Attributes
    assert metadata.get("status") == "Active", f"Expected status 'Active', got {metadata.get('status')}"
    assert metadata.get("priority") == "High", f"Expected priority 'High', got {metadata.get('priority')}"
