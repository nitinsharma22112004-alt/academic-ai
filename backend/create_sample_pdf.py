"""
Generate a valid multi-page PDF for testing and demonstration.
Creates DBMS_Notes.pdf containing authentic course notes.
"""

import os

def create_pdf(output_path: str):
    pages_text = [
        # Page 1
        [
            "Course: Database Management Systems (DBMS)",
            "Unit 1: Introduction to Relational Databases",
            "",
            "A Database Management System (DBMS) is software used to store, manage,",
            "and retrieve data efficiently. The relational model represents data",
            "in two-dimensional tables known as relations.",
            "",
            "Key Concepts:",
            "- Tuple: A single row in a relation representing a single record.",
            "- Attribute: A named column representing a property of the entity.",
            "- Domain: The set of allowable values for an attribute.",
            "- Primary Key: A candidate key chosen to uniquely identify tuples.",
            "- Foreign Key: An attribute that establishes a relationship by referencing",
            "  the primary key of another table."
        ],
        # Page 2
        [
            "Unit 2: Normalization in Relational Databases",
            "",
            "Normalization is a database design technique used to reduce data",
            "redundancy and improve data integrity by eliminating insertion,",
            "deletion, and update anomalies.",
            "",
            "Normal Forms:",
            "1. First Normal Form (1NF):",
            "   Every column must contain atomic (indivisible) values, and",
            "   there should be no repeating groups.",
            "",
            "2. Second Normal Form (2NF):",
            "   Must be in 1NF and eliminate partial functional dependency.",
            "   All non-key attributes must be fully functionally dependent",
            "   on the entire primary key.",
            "",
            "3. Third Normal Form (3NF):",
            "   Must be in 2NF and eliminate transitive dependency.",
            "   Non-prime attributes must not depend on other non-prime attributes.",
            "",
            "4. Boyce-Codd Normal Form (BCNF):",
            "   A stricter version of 3NF. For every non-trivial functional",
            "   dependency X -> Y, X must be a super key."
        ],
        # Page 3
        [
            "Unit 3: Transaction Processing and ACID Properties",
            "",
            "A transaction is an execution of a sequence of database operations",
            "treated as a single logical unit of work.",
            "",
            "ACID Properties:",
            "1. Atomicity: Either all operations are executed or none are (all-or-nothing).",
            "2. Consistency: Preserves database integrity constraints before and after execution.",
            "3. Isolation: Concurrent execution of transactions produces the same state as serial execution.",
            "4. Durability: Committed updates persist permanently even in the event of a power failure.",
            "",
            "Concurrency control protocols like Two-Phase Locking (2PL) and strict 2PL",
            "ensure conflict serializability and avoid cascading rollbacks."
        ]
    ]

    # Build pure PDF binary structure
    objects = []
    
    def add_object(content_str):
        objects.append(content_str)
        return len(objects)

    # Placeholder for catalog and pages
    font_obj_id = 3
    page_obj_ids = []
    content_obj_ids = []

    # Prepare stream content for each page
    for p_idx, lines in enumerate(pages_text):
        stream_lines = ["BT", "/F1 11 Tf", "50 750 Td", "16 TL"]
        for line in lines:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_lines.append(f"({safe_line}) '")
        stream_lines.append("ET")
        stream_content = "\n".join(stream_lines)
        stream_bytes = stream_content.encode("latin-1")
        
        c_obj = f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}\nendstream"
        content_obj_ids.append(c_obj)

    # 1 0 obj: Catalog
    catalog_str = "<< /Type /Catalog /Pages 2 0 R >>"
    
    # We will assemble objects:
    # 1: Catalog
    # 2: Pages root
    # 3: Font
    # 4, 6, 8...: Page objects
    # 5, 7, 9...: Content stream objects
    
    all_objs = [catalog_str, "PAGES_PLACEHOLDER", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    
    current_id = 4
    page_refs = []
    for c_idx, c_obj in enumerate(content_obj_ids):
        page_id = current_id
        content_id = current_id + 1
        current_id += 2
        
        page_refs.append(f"{page_id} 0 R")
        page_obj = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        all_objs.append(page_obj)
        all_objs.append(c_obj)
        
    pages_obj = f"<< /Type /Pages /Kids [ {' '.join(page_refs)} ] /Count {len(page_refs)} >>"
    all_objs[1] = pages_obj

    # Write PDF file with xref table
    with open(output_path, "wb") as f:
        f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, obj_str in enumerate(all_objs, start=1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n{obj_str}\nendobj\n".encode("latin-1"))
            
        xref_start = f.tell()
        f.write(f"xref\n0 {len(all_objs) + 1}\n".encode("latin-1"))
        f.write(b"0000000000 65535 f \n")
        for offset in offsets:
            f.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
            
        f.write(f"trailer\n<< /Size {len(all_objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("latin-1"))

    print(f"Generated sample study PDF: {output_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "DBMS_Notes.pdf")
    create_pdf(target)
