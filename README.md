#Required modules:

 - RDFLib (https://github.com/RDFLib/rdflib),
 - PDFMiner (http://www.unixuser.org/~euske/python/pdfminer/),
 - Grab (http://grablib.org/),
 - PyPDF2 (https://github.com/mstamy2/PyPDF2).
 
#Contacts

Maxim Kolchin (kolchinmax@gmail.com)
Fedor Kozlov (kozlovfedor@gmail.com)

#Queries

Prefixes that are used in the queries:

    PREFIX swrc:<http://swrc.ontoware.org/ontology#>
    PREFIX foaf:<http://xmlns.com/foaf/0.1/>
    PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dcterms:<http://purl.org/dc/terms/>
    PREFIX bibo:<http://purl.org/ontology/bibo/>
    PREFIX timeline:<http://purl.org/NET/c4dm/timeline.owl#>
    PREFIX swc:<http://data.semanticweb.org/ns/swc/ontology#>
    PREFIX dc:<http://purl.org/dc/elements/1.1/>
    PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
    PREFIX dbpedia-owl:<http://dbpedia.org/ontology/>


####Q1.1: List the full names of all editors of the proceedings of workshop W

    SELECT ?proc ?editor_name WHERE {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-1085/>
        <http://ceur-ws.org/Vol-1008/>
        <http://ceur-ws.org/Vol-1/>
      }
      ?proc   swrc:editor ?editor .
      ?editor foaf:name   ?editor_name .
    }

####Q1.2: Count the number of papers in workshop W

    SELECT ?proc (count(?pub) AS ?paper_count) {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-979/>
        <http://ceur-ws.org/Vol-1008/>
        <http://ceur-ws.org/Vol-994/>
        <http://ceur-ws.org/Vol-1/>
      }
      ?pub dcterms:partOf ?proc .
    }
    GROUP BY ?proc

####Q1.3: List the full names of all authors who have (co-)authored a paper in workshop W

    SELECT DISTINCT ?proc ?creator_name WHERE {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-1085/>
        <http://ceur-ws.org/Vol-994/>
      } .
      ?pub dcterms:partOf ?proc .
      ?creator dc:creator ?pub ;
               foaf:name ?creator_name .
    }

####Q1.4: Compute the average length (in numbers of pages) of a paper in workshop W

    SELECT (AVG(?pages) AS ?avg) {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-1085/>
        <http://ceur-ws.org/Vol-994/>
      }
      ?proc dcterms:hasPart ?pub .
      ?pub bibo:numPages ?pages .
    }
    GROUP BY ?proc

####Q1.5: Find out whether the proceedings of workshop W were published on CEUR-WS.org before the workshop took place

    SELECT ?proc ?result {
      VALUES ?proc {
         <http://ceur-ws.org/Vol-1085/>
         <http://ceur-ws.org/Vol-1/>
       }
       ?proc bibo:presentedAt ?workshop ;
             dcterms:issued ?issued .
       { ?workshop timeline:atDate ?date }
       UNION
       { ?workshop timeline:beginsAtDateTime ?date }
       BIND(bound(?date) && YEAR(?date) >= YEAR(?issued) && (MONTH(?date) = MONTH(?issued) && DAY(?date) >= DAY(?issued) || MONTH(?date) > MONTH(?issued)) AS ?result)
    }

####Q1.6: Identify all editions that the workshop series titled T has published with CEUR-WS.org

    SELECT (STRDT(?search, xsd:string) AS ?search_a) ?proc WHERE {
      VALUES ?search {"Linked Data on the Web" "Workshop on Modular Ontologies"}
      ?workshop a bibo:Workshop;
                rdfs:label ?label .
      ?proc a swrc:Proceedings ;
            bibo:presentedAt ?workshop .
      FILTER(strStarts(?label, ?search)) .
    }

####Q1.7: Identify the full names of those chairs of the workshop series titled T that have so far been a chair in every edition of the workshop that was published with CEUR-WS.org

    SELECT (STRDT(?search, xsd:string) AS ?search_a) ?editor_name WHERE {
      {
        SELECT ?search ?workshop ?editor WHERE {
          VALUES ?search {"Linked Data on the Web" "Semantic Publishing"} .
          ?workshop a bibo:Workshop;
                    rdfs:label ?label .
          FILTER(strStarts(?label, ?search)) .
          [] a swrc:Proceedings;
                               bibo:presentedAt ?workshop;
                               swrc:editor ?editor .
        }
      }
      {
        SELECT ?search (COUNT(?workshop) AS ?count) WHERE {
          VALUES ?search {"Linked Data on the Web" "Semantic Publishing"} .
          ?workshop a bibo:Workshop;
                    rdfs:label ?label .
          FILTER(strStarts(?label, ?search)) .
        }
        GROUP BY ?search
      }
      ?editor foaf:name ?editor_name .
    }
    GROUP BY ?search ?editor_name
    HAVING (COUNT(?search) = MAX(?count))

####Q1.8: Identify all CEUR-WS.org proceedings volumes in which papers of workshops of conference C in year Y were published

    SELECT ?conf_name (YEAR(?conf_year) AS ?conf_year_int) ?proc WHERE {
      {
        ?conf a swc:OrganizedEvent;
              rdfs:label "LPNMR"^^xsd:string ;
              rdfs:label ?conf_name ;
              timeline:atDate "2013"^^xsd:gYear ;
              timeline:atDate ?conf_year .
      }
      UNION
      {
        ?conf a swc:OrganizedEvent;
              rdfs:label "WWW"^^xsd:string ;
              rdfs:label ?conf_name ;
              timeline:atDate "2012"^^xsd:gYear ;
              timeline:atDate ?conf_year .
      }
      ?workshop a bibo:Workshop;
                swc:isSubEventOf ?conf .
      ?proc a swrc:Proceedings ;
            bibo:presentedAt ?workshop .
    }

####Q1.9: Identify those papers of workshop W that were (co-)authored by at least one chair of the workshop

    SELECT DISTINCT ?proc ?pub WHERE {
        VALUES ?proc {
            <http://ceur-ws.org/Vol-1008/>
            <http://ceur-ws.org/Vol-721/>
            <http://ceur-ws.org/Vol-1/>
        }
        ?proc swrc:editor ?editor .
        ?editor a foaf:Agent ;
                foaf:name ?editor_name .
        ?pub a foaf:Document ;
             dcterms:partOf ?proc .
        ?author a foaf:Agent ;
                dc:creator ?pub ;
                foaf:name ?author_name .
        FILTER(REGEX(?author_name, CONCAT(".*", REPLACE(?editor_name, "[. ']+", ".*"), ".*"), "i")) .
    }

####Q1.10: List the full names of all authors of invited papers in workshop W

    SELECT ?proc ?author_name {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-1085/>
        <http://ceur-ws.org/Vol-1081/>
        <http://ceur-ws.org/Vol-1008/>
      }
      ?proc dcterms:hasPart ?pub .
      ?pub a swc:InvitedPaper .
      ?author dc:creator ?pub ;
              foaf:name ?author_name .
    }

####Q1.11: Determine the number of editions that the workshop series titled T has had, regardless of whether published with CEUR-WS.org

    SELECT (STRDT(?prefix, xsd:string) AS ?prefix_a) (SUM(?edition) AS ?edition_count) {
      {
        SELECT ?prefix (MAX(?edition) AS ?max_edition) {
          VALUES ?prefix {
            "Linked Data on the Web"
            "Workshop on Modular Ontologies"
          }
          ?workshop a bibo:Workshop ;
            rdfs:label ?workshop_name .
          OPTIONAL { ?workshop swrc:edition ?e . }
          BIND (IF(bound(?e), ?e, 1) AS ?edition)
          FILTER(STRSTARTS(?workshop_name, ?prefix))
        }
        GROUP BY ?prefix
      }
      {
        SELECT ?prefix ?edition {
          VALUES ?prefix {
            "Linked Data on the Web"
            "Workshop on Modular Ontologies"
          }
          ?workshop a bibo:Workshop ;
            rdfs:label ?workshop_name .
          OPTIONAL { ?workshop swrc:edition ?e . }
          BIND (IF(bound(?e), ?e, 1) AS ?edition)
          FILTER(STRSTARTS(?workshop_name, ?prefix))
        }
      }
      FILTER(?max_edition = ?edition)
    }
    GROUP BY ?prefix

####Q1.12: Determine the title (without year) that workshop W had in its first edition

    SELECT ?proc ?prefix {
      {
        SELECT ?proc (MIN(?date) AS ?min_date) {
          VALUES ?proc {
            <http://ceur-ws.org/Vol-1049/>
          }
          ?proc bibo:presentedAt|bibo:presentedAt/skos:related ?workshop .
          { ?workshop timeline:atDate ?date . }
          UNION
          { ?workshop timeline:beginsAtDateTime ?date . }
        }
        GROUP BY ?proc
      }
      ?proc bibo:presentedAt|bibo:presentedAt/skos:related ?workshop .
      ?workshop rdfs:label ?name .
      { ?workshop timeline:atDate ?date . }
      UNION
      { ?workshop timeline:beginsAtDateTime ?date . }
      FILTER(?date = ?min_date)
      BIND(REPLACE(?name, "\\s+(20|19)\\d{2}.*$","") AS ?prefix)
    }

####Q1.13: Of the workshops of conference C in year Y, identify those that did not publish with CEUR-WS.org in the following year (and that therefore probably no longer took place)

    SELECT DISTINCT (STRDT(?acrn, xsd:string) AS ?acrn_str) (YEAR(?conf_date) AS ?conf_date_int) ?proc {
      VALUES (?acrn ?year) {
        ("ISWC" "2012")
      }
      ?conf a swc:OrganizedEvent ;
            rdfs:label ?conf_name ;
            timeline:atDate ?conf_date .
      ?workshop swc:isSubEventOf ?conf .
      ?proc bibo:presentedAt ?workshop .
      FILTER( ?conf_name = ?acrn && STR(YEAR(?conf_date)) = ?year )
      FILTER EXISTS { ?workshop skos:related [] . }
      FILTER NOT EXISTS { [] skos:related ?workshop . }
    }

####Q1.14: Identify the papers of the workshop titled T (which was published in a joint volume V with other workshops)

    SELECT (STRDT(?acrn, xsd:string) AS ?acrn_str) ?proc ?publication {
      VALUES (?acrn ?proc) {
        ("BeRSys" <http://ceur-ws.org/Vol-981/>)
      }
      ?workshop bibo:shortTitle ?w_title .
      ?publication a swrc:InProceedings ;
                   bibo:presentedAt ?workshop .
      FILTER(?w_title = ?acrn)
    }

####Q1.15: List the full names of all editors of the proceedings of the workshop titled T (which was published in a joint volume V with other workshops)

    SELECT (STRDT(?acrn, xsd:string) AS ?acrn_str) ?proc ?chair_name {
        VALUES (?acrn ?proc) {
            ("BeRSys" <http://ceur-ws.org/Vol-981/>)
        }
        ?w a bibo:Workshop ;
            rdfs:label | bibo:shortTitle ?w_name ;
            swc:hasRole / swc:heldBy ?chair .
        ?chair foaf:name ?chair_name .
        ?proc bibo:presentedAt ?w .
        FILTER(?w_name = ?acrn)
    }
    LIMIT 10

####Q1.16: Of the workshops that had editions at conference C both in year Y and Y+1, identify the workshop(s) with the biggest percentage of growth

    SELECT (STRDT(?acrn, xsd:string) AS ?acrn_str) (YEAR(?cr_date) AS ?date) ?pr {
      ?c a swc:OrganizedEvent ;
            rdfs:label ?c_name ;
            timeline:atDate ?c_date .
      ?cr a swc:OrganizedEvent ;
            rdfs:label ?cr_name ;
            timeline:atDate ?cr_date .
      ?w a bibo:Workshop ;
         swc:isSubEventOf ?c .
      ?wr skos:related ?w ;
          swc:isSubEventOf ?cr .
      ?p a swrc:Proceedings ;
         bibo:presentedAt ?w .
      ?pr a swrc:Proceedings ;
          bibo:presentedAt ?wr .
      {
        SELECT ?p (COUNT(?pub) AS ?p_num_pubs) {
          ?p dcterms:hasPart ?pub .
          ?pub a swrc:InProceedings .
        }
        GROUP BY ?p
      }
      {
        SELECT ?pr (COUNT(?pub) AS ?pr_num_pubs) {
          ?pr dcterms:hasPart ?pub .
          ?pub a swrc:InProceedings .
        }
        GROUP BY ?pr
      }
      {
        SELECT ?acrn ?year (MAX(?pr_num_pubs-?p_num_pubs) AS ?max_diff) {
            VALUES (?acrn ?year) {
            ("WWW" "2012")
          }
          ?c a swc:OrganizedEvent ;
                rdfs:label ?c_name ;
                timeline:atDate ?c_date .
          ?cr a swc:OrganizedEvent ;
                rdfs:label ?cr_name ;
                timeline:atDate ?cr_date .
          ?w a bibo:Workshop ;
             swc:isSubEventOf ?c .
          ?wr skos:related ?w ;
              swc:isSubEventOf ?cr .
          ?p a swrc:Proceedings ;
             bibo:presentedAt ?w .
          ?pr a swrc:Proceedings ;
              bibo:presentedAt ?wr .
          {
            SELECT ?p (COUNT(?pub) AS ?p_num_pubs) {
              ?p dcterms:hasPart ?pub .
              ?pub a swrc:InProceedings .
            }
            GROUP BY ?p
          }
          {
            SELECT ?pr (COUNT(?pub) AS ?pr_num_pubs) {
              ?pr dcterms:hasPart ?pub .
              ?pub a swrc:InProceedings .
            }
            GROUP BY ?pr
          }
          FILTER(?c_name = ?acrn && ?cr_name = ?acrn && STR(YEAR(?c_date)) = ?year && ?c_date < ?cr_date)
        }
        GROUP BY ?acrn ?year
      }
      FILTER(?c_name = ?acrn && ?cr_name = ?acrn && STR(YEAR(?c_date)) = ?year && ?c_date < ?cr_date && (?pr_num_pubs - ?p_num_pubs) = ?max_diff)
    }

####Q1.17: Return the acronyms of those workshops of conference C in year Y whose previous edition was co-located with a different conference series.

    SELECT (STRDT(?acrn, xsd:string) AS ?acrn_str) (YEAR(?c_date) AS ?c_year) ?w_name {
      VALUES (?acrn ?year) {
        ("ISWC" "2012")
      }
      ?c a swc:OrganizedEvent ;
         rdfs:label ?c_name ;
         timeline:atDate ?c_date .
      ?w a bibo:Workshop ;
         swc:isSubEventOf ?c ;
         rdfs:label ?w_name .
      {
        SELECT ?w (MAX(?date) AS ?prev_date) {
          ?wr a bibo:Workshop ;
              timeline:atDate | timeline:beginsAtDateTime ?date .
          ?w skos:related ?wr .
        }
        GROUP BY ?w
      }
      ?w skos:related ?wr .
      ?wr timeline:atDate | timeline:beginsAtDateTime ?wr_date ;
          swc:isSubEventOf ?cr .
      ?cr a swc:OrganizedEvent ;
          rdfs:label ?cr_name .
      FILTER(?c_name = ?acrn && STR(YEAR(?c_date)) = ?year && ?cr_name != ?acrn &&
    ?wr_date = ?prev_date)
    }

####Q1.18: Of the workshop series titled T, identify those editions that took place more than two months later/earlier than the previous edition that was published with CEUR-WS.org

    SELECT (STRDT(?prefix, xsd:string) AS ?prefix_str) (YEAR(?prev) AS ?p) (YEAR(?date) AS ?d) {
      {
        SELECT ?prefix ?x (MAX(?y_date) as ?prev) {
          VALUES ?prefix {
            "Linked Data on the Web"
            "Workshop on Modular Ontologies"
          }
          ?x a bibo:Workshop ;
             rdfs:label ?x_name ;
             timeline:atDate|timeline:beginsAtDateTime ?x_date .
          ?y a bibo:Workshop ;
             rdfs:label ?y_name ;
             timeline:atDate|timeline:beginsAtDateTime ?y_date .
          FILTER(
            STRSTARTS(?x_name, ?prefix)
            && STRSTARTS(?y_name, ?prefix)
            && ?x_date > ?y_date
          )
        }
        GROUP BY ?prefix ?x
      }
      ?x timeline:atDate|timeline:beginsAtDateTime ?date .
      FILTER(ABS(MONTH(?date) - MONTH(?prev))>=2)
    }

####Q1.19: Identify all countries that the authors of all regular papers in workshop W were from

    SELECT DISTINCT ?proc ?country {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-800/>
        <http://ceur-ws.org/Vol-1/>
      }
      ?proc dcterms:hasPart ?pub .
      ?pub dbpedia-owl:country ?country .
    }

####Q1.20: Identify those papers in workshop W that were (co-)authored by people from the same institution as one of the chairs (including papers by chairs)

    SELECT * {
      VALUES ?proc {
        <http://ceur-ws.org/Vol-1081/>
        <http://ceur-ws.org/Vol-315/>
      }
      ?proc dcterms:hasPart ?pub ;
            swrc:affiliation ?affiliation .
      ?pub swrc:affiliation ?affiliation .
    }

 
