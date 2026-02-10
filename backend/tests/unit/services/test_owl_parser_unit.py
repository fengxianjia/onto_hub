import os
import json
from app.services.parsers.owl_parser import OWLParser
from app.models import OntologyFile

TTL_CONTENT = """
@prefix : <http://example.org/onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:Animal a owl:Class ;
    rdfs:label "Animal" .

:Dog a owl:Class ;
    rdfs:label "Dog" ;
    rdfs:subClassOf :Animal .
"""

def test_owl_parser_unit():
    parser = OWLParser()
    file_record = OntologyFile(file_path="test.ttl")
    rules = {}
    
    entities = parser.parse(file_record, TTL_CONTENT, rules)
    
    # 验证是否提取到了类
    names = [e["name"] for e in entities]
    assert "Animal" in names
    assert "Dog" in names
    
    # 验证关系 (Dog subClassOf Animal)
    dog_entity = next(e for e in entities if e["name"] == "Dog")
    assert "Animal" in dog_entity["links"]
    
    print("OWL Unit Test Passed!")

if __name__ == "__main__":
    test_owl_parser_unit()
