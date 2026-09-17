"""
Populate Qdrant with Comprehensive Regulatory Knowledge for TradeRule AI.
Includes IMDG code, SOLAS container packing, US CBP regulations, customs clearance,
export licensing, carrier rules, chemical transit, and platform guides.
"""

import json
import os
import sys
import uuid
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
load_dotenv(SRC_DIR.parent.parent / ".env")

import requests
from context_augmentation import create_embedding_client, embed_query

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "traderule_rag_chunks")
CHUNK_ID_NAMESPACE = uuid.UUID("7b8f4d2a-8f3e-4a9a-9f2c-5d1c7e9b2a11")

REGULATORY_DOCUMENTS = [
    # -------------------------------------------------------------
    # 1. IMDG Code Amendment 41-22 & Lithium-Ion Batteries
    # -------------------------------------------------------------
    {
        "source": "IMDG_Code_Amendment_41-22.pdf",
        "document_type": "Maritime Regulation",
        "section": "Section 3.4 / Special Provision 188 & 230",
        "chunk_id": "imdg-battery-ocean-01",
        "text": (
            "Under the International Maritime Dangerous Goods (IMDG) Code Amendment 41-22 (Section 3.4), "
            "UN3481 lithium-ion batteries packed with equipment or contained in equipment are fully permitted "
            "for ocean freight transport into United States and international ports. Shipper compliance requires "
            "that lithium-ion cells and batteries meet the standard State of Charge (SOC) limitation not exceeding 30% "
            "of their rated design capacity. In addition, outer packaging must bear the proper Class 9 Lithium Battery "
            "hazard label, UN specification markings, and be accompanied by a signed Dangerous Goods Declaration (DGD)."
        ),
    },
    {
        "source": "IMDG_Code_Amendment_41-22.pdf",
        "document_type": "Maritime Regulation",
        "section": "Special Provision 376 / Damaged & Defective Cells",
        "chunk_id": "imdg-battery-ocean-02",
        "text": (
            "IMDG Code Special Provision 376 establishes strict restrictions for damaged, defective, or recalled "
            "lithium-ion batteries. Such batteries are strictly prohibited from standard ocean cargo transport unless "
            "packaged in specialized flame-retardant hermetically sealed containers approved by the competent maritime authority. "
            "All ocean shipments containing UN3480 (lithium-ion batteries alone) or UN3481 must clearly specify the UN number "
            "on the ocean Bill of Lading and manifest."
        ),
    },

    # -------------------------------------------------------------
    # 2. SOLAS Chapter VII Regulation 5 / Container Packing Certificate
    # -------------------------------------------------------------
    {
        "source": "SOLAS_Chapter_VII_Carriage_of_Dangerous_Goods.pdf",
        "document_type": "International Convention",
        "section": "Chapter VII Regulation 5 / CPC Verification",
        "chunk_id": "solas-cpc-cert-01",
        "text": (
            "Under the International Convention for the Safety of Life at Sea (SOLAS) Chapter VII Regulation 5, "
            "a signed Container/Vehicle Packing Certificate (CPC) is legally mandatory for all freight containers "
            "containing dangerous goods before loading aboard ship. The packing certificate certifies that the container "
            "was clean, dry, and structurally fit; that incompatible goods have been properly segregated according to IMDG segregation tables; "
            "that all packages have been inspected and secured; and that cargo weight is evenly distributed within certified limits."
        ),
    },

    # -------------------------------------------------------------
    # 3. Regional Port Rulings & Transit Tax Implications
    # -------------------------------------------------------------
    {
        "source": "Port_Transit_and_Customs_Tax_Rulings.pdf",
        "document_type": "Tax & Customs Advisory",
        "section": "Port Authority Transit Rulings",
        "chunk_id": "port-tax-transit-01",
        "text": (
            "Regional port tax and tariff implications: Inconclusive ruling records exist for regional state or local "
            "port tax exemptions under individual municipal port schedules. While goods moving in continuous international transit "
            "under customs bond are generally immune from state ad valorem property taxes pursuant to the US Constitution Import-Export Clause, "
            "local port authorities assess wharfage, terminal handling charges (THC), and harbor maintenance fees. Manual verification "
            "with the local port authority finance office and licensed customs broker is recommended for specific port terminals."
        ),
    },

    # -------------------------------------------------------------
    # 4. US Customs Entry Declarations & 19 CFR 12.3
    # -------------------------------------------------------------
    {
        "source": "CBP_Customs_Bulletin_Vol60.pdf",
        "document_type": "Customs Regulation",
        "section": "19 CFR 12.3 & Entry Declaration Formalities",
        "chunk_id": "cbp-entry-declaration-01",
        "text": (
            "Under U.S. Customs and Border Protection regulations (CBP Reg 19 CFR 12.3 and 19 CFR Part 141), "
            "all commercial shipments entering the United States require formal entry declarations. Importers must submit "
            "CBP Form 7501 (Entry Summary) and CBP Form 3461 (Entry/Immediate Delivery) electronically via the Automated Commercial Environment (ACE). "
            "Required declaration documents include the commercial invoice showing buyer, seller, currency, terms of sale (Incoterms), "
            "10-digit Harmonized Tariff Schedule (HTSUS) classification, packing list, bill of lading, and evidence of a valid continuous customs bond."
        ),
    },
    {
        "source": "CBP_Customs_Bulletin_Vol60.pdf",
        "document_type": "Customs Regulation",
        "section": "19 CFR 142.3 / Documentation Requirements",
        "chunk_id": "cbp-customs-clearance-docs-02",
        "text": (
            "Customs clearance documentation requirements for commercial entry: The mandatory documents for customs clearance "
            "are the commercial invoice, packing list detailing piece count and gross/net weights, bill of lading or air waybill (AWB), "
            "certificate of origin, and applicable partner government agency (PGA) licenses (such as EPA, FDA, or FCC declarations). "
            "Failure to present complete customs clearance documentation within 15 calendar days of arrival may result in goods "
            "being transferred to General Order (GO) warehouse storage."
        ),
    },

    # -------------------------------------------------------------
    # 5. Export Guidelines & Licensing Requirements
    # -------------------------------------------------------------
    {
        "source": "export_guidelines.md",
        "document_type": "Export Controls Guide",
        "section": "Export Licensing & Dual-Use Restrictions",
        "chunk_id": "export-licensing-rules-01",
        "text": (
            "When does an exporter need an export license? An exporter must obtain a validated export license before dispatch "
            "whenever a product is designated under the Commerce Control List (CCL) with an Export Control Classification Number (ECCN), "
            "when the commodity is controlled for national security, regional stability, or chemical/biological proliferation reasons, "
            "when shipping to restricted destinations or embargoed countries, or when the end-user appears on the Consolidated Screening List (CSL). "
            "Exporters must file Electronic Export Information (EEI) through the Automated Export System (AES) for shipments exceeding $2,500."
        ),
    },
    {
        "source": "customs_requirements.txt",
        "document_type": "Customs Requirement",
        "section": "Export Control & Clearance",
        "chunk_id": "customs-general-clearance-01",
        "text": (
            "International shipment compliance requires exporters and importers to verify product classification, destination requirements, "
            "customs documentation, and applicable export controls before dispatch. The exporter must confirm customs declarations, "
            "commercial invoice details, harmonized tariff codes, and ensure that all necessary permits and clearance certificates are present."
        ),
    },

    # -------------------------------------------------------------
    # 6. TradeRule AI Platform & Capabilities
    # -------------------------------------------------------------
    {
        "source": "TradeRule_AI_System_Guide.md",
        "document_type": "Platform Documentation",
        "section": "System Architecture & Compliance Overview",
        "chunk_id": "traderule-platform-overview-01",
        "text": (
            "TradeRule AI is an enterprise-grade trade compliance intelligence platform designed for global logistics operators, "
            "freight forwarders, and trade compliance officers. It automates regulatory rule evaluation, shipment context intake "
            "(origin, destination, cargo classification, carrier, transport mode), grounded retrieval-augmented generation (RAG), "
            "citation attribution to official treaties and customs statutes, and real-time hallucination guardrails to ensure audit-proof decisions."
        ),
    },

    # -------------------------------------------------------------
    # 7. Carrier Compliance Agreements (Maersk, MSC, DHL, FedEx)
    # -------------------------------------------------------------
    {
        "source": "Carrier_Agreements_and_Routing_Guide.md",
        "document_type": "Carrier Policy",
        "section": "Maersk Line Ocean Carriage Rules",
        "chunk_id": "carrier-maersk-ocean-01",
        "text": (
            "Maersk Line Ocean Transport Agreement (Asia to United States lanes): Shipper must submit final Dangerous Goods Declaration (DGD) "
            "and Container Packing Certificate (CPC) no later than 48 hours prior to vessel cutoff. For lithium-ion battery shipments (UN3480/UN3481), "
            "Maersk requires certified proof that state of charge is under 30% and that packaging conforms to UN packaging group II specifications. "
            "Containers exceeding payload limits or showing improper weight distribution will be rejected at terminal gate."
        ),
    },
    {
        "source": "Carrier_Agreements_and_Routing_Guide.md",
        "document_type": "Carrier Policy",
        "section": "MSC Mediterranean Europe to Canada Rules",
        "chunk_id": "carrier-msc-canada-02",
        "text": (
            "MSC Mediterranean Shipping Guidelines (Europe to Canada lanes): Requires advance electronic cargo manifest filing (ACI eManifest) "
            "at least 24 hours prior to loading at the European port of departure. Shipments containing industrial chemicals or dangerous goods "
            "must provide an international Safety Data Sheet (SDS) in English and French, 24-hour emergency telephone contact number, "
            "and marine pollutant notification."
        ),
    },
    {
        "source": "Carrier_Agreements_and_Routing_Guide.md",
        "document_type": "Carrier Policy",
        "section": "DHL Global Forwarding Air Freight Rules",
        "chunk_id": "carrier-dhl-airfreight-03",
        "text": (
            "DHL Global Forwarding Air Cargo Terms: All air freight must strictly comply with ICAO Technical Instructions and IATA Dangerous "
            "Goods Regulations (DGR). Lithium-ion batteries UN3480 transported as cargo are forbidden on passenger aircraft and must carry the "
            "'Cargo Aircraft Only' (CAO) label. Maximum net quantity per package restrictions apply. Shippers must present Air Waybill (AWB) "
            "and complete shipper's declaration for dangerous goods."
        ),
    },
    {
        "source": "Carrier_Agreements_and_Routing_Guide.md",
        "document_type": "Carrier Policy",
        "section": "FedEx Express US to Australia Rules",
        "chunk_id": "carrier-fedex-australia-04",
        "text": (
            "FedEx Express United States to Australia Agreement: All consignments bound for Australia must comply with Australian Border Force (ABF) "
            "and Department of Agriculture, Fisheries and Forestry (DAFF) biosecurity import regulations. Commercial invoices must specify value in AUD "
            "or USD with detailed breakdown of freight and insurance. Timber packaging must be ISPM 15 heat treated and stamped."
        ),
    },

    # -------------------------------------------------------------
    # 8. Industrial Chemicals & Restricted Goods Transit
    # -------------------------------------------------------------
    {
        "source": "Industrial_Chemicals_Transit_Compliance.md",
        "document_type": "Hazardous Materials Manual",
        "section": "Chemical Compound Transit & Documentation",
        "chunk_id": "chemical-transit-rules-01",
        "text": (
            "Industrial chemical compounds and hazardous substances transit requirements: Any international shipment containing chemical compounds "
            "requires a 16-section Safety Data Sheet (SDS) conforming to the Globally Harmonized System (GHS), a signed Dangerous Goods Declaration (DGD), "
            "proper UN identification number, packaging group assignment (PG I, PG II, or PG III), and technical chemical name. Exporters must verify "
            "Toxic Substances Control Act (TSCA) import/export certification for US routes and REACH registration for European transit."
        ),
    },

    # -------------------------------------------------------------
    # 9. Textiles, Apparel Tariffs & Quotas
    # -------------------------------------------------------------
    {
        "source": "Textile_Quotas_and_Tariff_Classification_Guide.md",
        "document_type": "Tariff Classification Manual",
        "section": "Apparel Classification & Rules of Origin",
        "chunk_id": "textile-tariff-rules-01",
        "text": (
            "Textiles and apparel import compliance: Importers of textile goods must declare exact fiber composition percentages by weight, "
            "gender/age category, and fabric construction (knitted or woven) under Chapter 61 and 62 of the Harmonized Tariff Schedule. "
            "Shipments claiming preferential tariff treatment require a valid Certificate of Origin demonstrating yarn-forward or "
            "fabric-forward rules of origin compliance under applicable free trade agreements."
        ),
    },
]


def create_deterministic_uuid(chunk_id: str) -> str:
    return str(uuid.uuid5(CHUNK_ID_NAMESPACE, chunk_id))


def populate():
    print("=" * 60)
    print("TradeRule AI Knowledge Base Populator")
    print("=" * 60)

    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    headers = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        headers["api-key"] = QDRANT_API_KEY

    # Check collection
    res = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", headers=headers)
    if not res.ok:
        print(f"Collection {COLLECTION_NAME} does not exist. Creating...")
        create_payload = {
            "vectors": {
                "size": 3072,
                "distance": "Cosine",
            }
        }
        create_res = requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", headers=headers, json=create_payload)
        create_res.raise_for_status()
        print(f"Created collection {COLLECTION_NAME}")

    embedding_client = create_embedding_client()
    print(f"Embedding client initialized. Preparing {len(REGULATORY_DOCUMENTS)} documents...")

    points_to_insert = []
    for idx, doc in enumerate(REGULATORY_DOCUMENTS, start=1):
        chunk_id = doc["chunk_id"]
        text = doc["text"]
        print(f"[{idx}/{len(REGULATORY_DOCUMENTS)}] Embedding chunk: {chunk_id} ({doc['source']})...")
        vector = embed_query(embedding_client, text)

        point_uuid = create_deterministic_uuid(chunk_id)
        points_to_insert.append({
            "id": point_uuid,
            "vector": vector,
            "payload": {
                "chunk_id": chunk_id,
                "text": text,
                "source": doc["source"],
                "document": doc["source"],
                "document_type": doc["document_type"],
                "section": doc["section"],
                "chunk_index": idx,
                "metadata": {
                    "source": doc["source"],
                    "document": doc["source"],
                    "section": doc["section"],
                    "document_type": doc["document_type"],
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                },
            },
        })

    # Insert batch into Qdrant
    print(f"Inserting {len(points_to_insert)} vector points into Qdrant...")
    insert_res = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true",
        headers=headers,
        json={"points": points_to_insert},
    )
    insert_res.raise_for_status()
    print("Insertion complete!")

    # Verify count
    count_res = requests.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/count", headers=headers, json={"exact": True})
    total_count = count_res.json()["result"]["count"]
    print(f"Total points now in '{COLLECTION_NAME}': {total_count}")
    print("Knowledge base successfully populated!")


if __name__ == "__main__":
    populate()
