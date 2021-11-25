import os, json, sys
import concurrent.futures

from graphqlclient import GraphQLClient
from urllib import request, parse, error


class questAssetGatherer:
    # section_id = "1888816384764129"  # all section
    section_id = "226705144927006"  # new section
    region = 'eu'
    graph_url = 'https://graph.oculus.com/graphql?forced_locale=en_US'
    file_oculus_appnames = "appnames_quest_graph.json"
    hmdType = "MONTEREY"  # Quest1&2 codename

    appWorkers = 1

    def __init__(self, args, oculus_asset_path):
        # use oculus_token file if no access token in arguments
        if not hasattr(args, "oculus_token") or args.oculus_token == "":
            if os.path.isfile(os.path.join("oculus_token")):
                print("use oculus_token file")
                with open(os.path.join("oculus_token")) as f:
                    first_line = f.readline()
                args.oculus_token = first_line
                if not args.oculus_token or args.oculus_token == "":
                    print("ERROR: oculus_token file is empty")
                    exit(1)
            else:
                print("ERROR: add your oculus access token as argument or create a oculus_token file")
                exit(1)

        self.oculus_token = args.oculus_token
        self.oculus_download_path = oculus_asset_path

        if (not os.path.isdir(oculus_asset_path)):
            os.mkdir(oculus_asset_path)

    def generate_appnames(self):
        print(f"self.oculus_token => {self.oculus_token}")
        print(f"section_id => {self.section_id}")
        print(f"oculus_download_path => {self.oculus_download_path}")

        headers = {
            "Origin": "https://www.oculus.com",
            "Referer": "https://www.oculus.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"
        }

        req = request.Request(self.graph_url)
        if headers:
            for key, value in headers.items():
                # print(key, '->', value)
                req.add_header(key, value)

        oculus_data = self.paginateSection(req)

        print(f"paginateSection done, got {len(oculus_data)} apps")
        if len(oculus_data) > 0:

            self.get_oculus_app_data(req, oculus_data[3], 3)


            exit(0)
            processes = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.appWorkers) as executor:
                for idx, oculus_app in enumerate(oculus_data):
                    # if category['name'] != "All":
                    #     continue
                    # print(f"{idx} => {category}")
                    print(f"Doing {idx} => {oculus_app['node']['display_name']}...")

                    processes.append(executor.submit(self.get_oculus_app_data, req, oculus_app, idx))

                    # print(res)
                    # concurrent.futures.wait(res)
                    # APPNAMES_SIDEQUEST_DATA = APPNAMES_SIDEQUEST_DATA + appnames_sidequest_data_sub

                concurrent.futures.wait(processes, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

                for _ in concurrent.futures.as_completed(processes):
                    result = _.result()
                    # print('Result: ', result)
        else:
            print("oculus_data is empty")
            exit(1)

        print("GenerateAppnames done")

    def paginateSection(self, req, oculus_data=False, page=1, limit="500", section_cursor="null"):
        print(f"paginateSection page {page} for section_cursor {section_cursor}")

        form_data = {
            "access_token": self.oculus_token,
            "variables": json.dumps({
                "sectionId": self.section_id,
                "sortOrder": "release_date",
                "sectionItemCount": limit,
                "sectionCursor": section_cursor,
                "hmdType": self.hmdType,
            }),
            "doc_id": "3821696797949516"
        }
        # print(f"form_data => {form_data}")

        req.data = parse.urlencode(form_data).encode()

        response = False
        print(f"sending...")
        try:
            response = request.urlopen(req)

        except:
            print("ERROR: oculus graph error: ")
            print(request)
            print("Unexpected error:", sys.exc_info()[0])
            exit(1)

        # print(f"received...")
        resBody = response.read().decode('utf-8')

        # print(f"json2obj...")
        apps = json.loads(resBody)
        if not apps:
            print(f'Loading for section_cursor {section_cursor} FAILED: (json) data empty')
            exit(1)

        print(f"Found {apps['data']['node']['all_items']['count']} total in section_id {self.section_id}")
        print(f"Found {len(apps['data']['node']['all_items']['edges'])} in section_cursor {section_cursor}")

        if len(apps['data']['node']['all_items']['edges']) > 0:
            if not oculus_data:
                oculus_data = apps['data']['node']['all_items']['edges']
            else:
                oculus_data += apps['data']['node']['all_items']['edges']

        if apps['data']['node']['all_items']['page_info']['has_next_page']:
            print(f"next section...")
            page += 1
            section_cursor = apps['data']['node']['all_items']['page_info']['end_cursor']
            oculus_data = self.paginateSection(req, oculus_data, page, limit, section_cursor)

        return oculus_data

    def get_oculus_app_data(self, req, oculus_app, idx):

        print(f"get_oculus_app_data idx {idx} for app {oculus_app['node']['display_name']}")

        # params = {  # QUEST APP
        #     'access_token': self.oculus_token
        #     ,
        #     'variables': '{"itemId":"' + appID + '","first":5,"last":null,"after":null,"before":null,"forward":true,
        #     "ordering":null,"ratingScores":null,"hmdType":"' + hmdType + '"}'
        #     , 'doc_id': '4136219906435554'
        # }

        form_data = {
            "access_token": self.oculus_token,
            "variables": json.dumps({
                "itemId": oculus_app['node']['id'],
                "hmdType": self.hmdType,
                "fields": "latest_supported_binary.package_name",
            }),
            "fields": "latest_supported_binary.package_name",
            "doc_id": "4136219906435554"  # product detail page
        }
        # print(f"form_data => {form_data}")

        req.data = parse.urlencode(form_data).encode()

        response = False
        print(f"sending...")
        try:
            response = request.urlopen(req)

        except:
            print("ERROR: oculus graph error: ")
            print(request)
            print("Unexpected error:", sys.exc_info()[0])
            exit(1)

        print(f"received...")
        resBody = response.read().decode('utf-8')

        print(f"json2obj...")
        app = json.loads(resBody)
        if not app:
            print(f"Loading for idx {idx} for app {oculus_app['node']['display_name']} FAILED: (json) data empty")
            exit(1)

        app['data']['node']['firstQualityRatings'] = "REMOVED"
        print(app['data']['node']['latest_supported_binary'])
        print(app['data']['node'])
        #TODO: apk name is missing in data, try https://github.com/if1live/oculus-graph/blob/master/lib/oculus.js
        exit(0)
        return app

        # APPNAMES_OCULUS_DATA[sidequest_entry["packagename"]] = {
        #     "name": sidequest_entry["name"],
        #     "category": catname,
        #     "category2": "",
        # }

        # if oculus_app["node"][''] in APPNAMES_OCULUS_DATA:
        #     if APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] == "" or \
        #             APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] == "SideQuest":
        #         APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] = catname
        #
        #     else:
        #         if APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] == "" or \
        #                 APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] == "SideQuest":
        #             APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] = catname
        #
        # else:
        #     APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]] = {
        #         "name": sidequest_entry["name"],
        #         "category": catname,
        #         "category2": "",
        #     }

        # return app_data
