from configs import configure_setup
from job_pydantic import JobKnowledgeGraph
from utils.cypher_utils import make_cypher_query
from process_data import get_job_desc
from datetime import date
import logging
import logging.handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "logs/update_kg.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

if __name__ == "__main__":
    knowledge_graph, client = configure_setup()

    # Example job description
    # with open("jd_example.txt", "r") as file:
    #     job_description = file.read()
    #

    # knowledge_graph.refresh_schema()
    # print(knowledge_graph.schema)

    with open("cypher/count_nodes.cypher", "r") as file:
        count_nodes_cypher = file.read()

    with open("cypher/count_relationships.cypher", "r") as file:
        count_relations_cypher = file.read()


    # with open("cypher/delete_all.cypher", "r") as file:
    #     delete_cypher = file.read()

    # knowledge_graph.query(delete_cypher)

    filename = f"job_posts_data/job_posts_artificial_intelligence_{str(date.today())}.json"
    # filename = f"job_posts_data/job_posts_artificial_intelligence_2024-06-03.json"

    n_processed = 0
    job_desc = get_job_desc(filename)
    for jd_info in job_desc:
        try:
            job_title, company_name, job_desc = jd_info
            job_desc = job_desc.replace('"', "'")

            system_prompt = f"""
            Help me understand the following by describing it as a detailed knowledge graph.
            Only extract and present only the factual information.
            Always return results in capitalized form
            
            Job descriptions: {job_desc}
            """

            resp = client.chat.completions.create(
            messages=[
                    {
                        "role": "user",
                        "content": system_prompt
                    }
                ],
                response_model= JobKnowledgeGraph,
            )

            cypher = make_cypher_query(resp, job_title, company_name)
            knowledge_graph.query(cypher)
            print(f"Added {job_title} @ {company_name} to Knowledge Graph.")
            logger.info(f"Added {job_title} @ {company_name} to Knowledge Graph.")

            n_processed += 1
        except Exception as e:
            print(e)
            logger.info(e)
            continue


    print(f"Processed {n_processed} job postings!")

    num_node = knowledge_graph.query(count_nodes_cypher)
    num_relation = knowledge_graph.query(count_relations_cypher)

    print(num_node[0], num_relation[0])
    logger.info(num_node[0])
    logger.info(num_relation[0])

