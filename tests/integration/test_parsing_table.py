import pytest
import time
import zipfile
import json

@pytest.fixture
def table_zip(tmp_path):
    """Creates a zip file with markdown content containing a table."""
    p = tmp_path / "table_test.zip"
    
    md_content = """---
type: Entity
---
# AO Operation

## Properties

| Display Name | Type | Primary Key | Description |
| :--- | :--- | :--- | :--- |
| AO Code | String | Yes | Unique ID |
| AO Name | String | No | Operation Name |
"""

    with zipfile.ZipFile(p, "w") as z:
        z.writestr("AO Operation.md", md_content)
        
    return str(p)

def test_parsing_table_rows(client, unique_code, table_zip):
    print(f"Testing table parsing for {unique_code}")
    
    # 1. Create Parsing Template with Table Strategy
    rules = {
        "entity": {
            "name_source": "filename_no_ext",
            "category_source": "frontmatter:type"
        },
        "attribute": {
            "strategies": [
                {
                    "type": "table_row",
                    "target_key": "properties",
                    "header_mapping": {
                        "Display Name": "name",
                        "Type": "dataType",
                        "Primary Key": "isPk",
                        "Description": "desc"
                    }
                }
            ]
        }
    }
    
    template_name = f"Template-Table-{unique_code}"
    template = client.create_template(name=template_name, rules=rules)
    template_id = template['id']
    print(f"Created template {template_id}")
    
    # 2. Create Ontology
    v1 = client.create_ontology(table_zip, code=unique_code, name="Table Test", template_id=template_id)
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
    
    # Check Properties
    properties = metadata.get("properties")
    assert properties is not None, "Properties should not be None"
    assert isinstance(properties, list), "Properties should be a list"
    assert len(properties) == 2, "Should have 2 rows"
    
    row1 = properties[0]
    assert row1["name"] == "AO Code"
    assert row1["dataType"] == "String"
    assert row1["isPk"] == "Yes"
    
    row2 = properties[1]
    assert row2["name"] == "AO Name"
    assert row2["dataType"] == "String"
    assert row2["isPk"] == "No"
