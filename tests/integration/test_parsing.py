import pytest
import os
import time
import zipfile
import json

@pytest.fixture
def parsing_zip(tmp_path):
    """Creates a zip file with markdown content for parsing."""
    p = tmp_path / "parsing_test.zip"
    
    # 1. ConceptA: depends on ConceptB
    md_a = """---
type: Concept
---
# Concept A
This is a description.
It depends on [[Concept B]].
"""

    # 2. ConceptB: has no dependencies
    md_b = """---
type: System
---
# Concept B
This is a base system.
"""

    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Concept A.md", md_a)
        z.writestr("Concept B.md", md_b)
        
    return str(p)

def test_parsing_flow(client, unique_code, parsing_zip):
    print(f"Testing parsing flow for {unique_code}")
    
    # 1. Create Parsing Template
    rules = {
        "entity": {
            "name_source": "filename_no_ext", # Should extract "Concept A" and "Concept B"
            "category_source": "frontmatter:type" # Should extract "Concept" and "System"
        },
        "relation": {
            "strategies": ["wikilink"] # Should match [[Concept B]]
        }
    }
    template_name = f"Template-{unique_code}"
    template = client.create_template(name=template_name, rules=rules)
    template_id = template['id']
    print(f"Created template {template_id}")
    
    # 2. Create Ontology with Template
    v1 = client.create_ontology(parsing_zip, code=unique_code, name="Parsing Test", template_id=template_id)
    v1_id = v1['id']
    print(f"Created ontology {v1_id}")
    
    # 3. Wait for Parsing
    print("Waiting for parsing...")
    nodes = []
    links = []
    for i in range(10):
        time.sleep(2) # Wait 2s
        graph = client.get_ontology_graph(v1_id)
        nodes = graph.get("nodes", [])
        links = graph.get("links", [])
        if len(nodes) >= 2:
            break
            
    # 4. Assertions
    print(f"Nodes: {len(nodes)}, Links: {len(links)}")
    assert len(nodes) == 2, "Should have 2 nodes"
    # assert len(links) == 1, "Should have 1 link" 
    # Link might be 0 if regex didn't match or resolution failed. 
    # Let's debug if it fails.
    
    # Verify Node Names
    names = [n['name'] for n in nodes]
    print(f"Extracted Names: {names}")
    assert "Concept A" in names
    assert "Concept B" in names
    
    if len(links) > 0:
        # Verify Link
        link = links[0]
        node_map = {n['id']: n['name'] for n in nodes}
        source_name = node_map.get(link['source_id'])
        target_name = node_map.get(link['target_id'])
        
        print(f"Link: {source_name} -> {target_name} ({link['relation_type']})")
        assert source_name == "Concept A"
        assert target_name == "Concept B"
        assert link['relation_type'] == "related_to"
    else:
        pytest.fail("Link not found between Concept A and Concept B")

