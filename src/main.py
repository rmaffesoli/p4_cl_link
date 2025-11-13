#!/usr/bin/env python
import logging
import argparse
import re
import os
from P4 import P4, P4Exception
from p4_cl_link import environment

from dam_api.write_weblink import attach_weblink

P4_PORT = os.environ.get('P4PORT')
P4_USER = os.environ.get('P4USER')

p4 = P4()
p4.user = P4_USER
p4.port = P4_PORT
p4.connect()


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def gather_changelist_links(description):
    weblink_pattern = r"(?<=\()http[^\)]*(?=\))"
    weblink_matches = re.findall(weblink_pattern, description)
    return weblink_matches

def gather_cr_links(description):
    review_pattern = r"(?!#review-)\d+"
    review_matches = re.match(review_pattern, description)
    return review_matches

def main(changelist):
    changelist_list = p4.run_describe(changelist)
    description = changelist_list[0]['desc']
    depot_files = changelist_list[0]['depotFile']
    
    cl_weblinks = gather_changelist_links(description)
    cl_review_links = gather_cr_links(description)
    print('cl_weblinks',cl_weblinks)
    print('cl_review_links',cl_review_links)

    # print(changelist_list)
    for depot_file in depot_files:
        for weblink in cl_weblinks: 
            attach_weblink(depot_file, weblink)


    # file_process_dict: dict = claude_api_trigger.gather_file_process_list(changelist)

    # logger.info(
    #     f"Processing changelist {changelist}. {len(file_process_dict['file_list'])} files to process."
    # )

    # ai_results = tagging_ai.process_changelist(file_process_dict)

    # for result in ai_results:
    #     attach_metadata(
    #         result["depot_path"], "image description", result["description"]
    #     )
    #     attach_additional_tags(result["depot_path"], result["tags"])

    # logger.info(ai_results)
    # return ai_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("changelist")

    parsed_args = parser.parse_args()
    main(parsed_args.changelist)
