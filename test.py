import requests

body = """query teamList {
  teamList {
    id
    code
    name_ch
    name_en
  }
}"""

body2 = """query tournamentList {
  tournamentList {
    id
    frontEndId
    nameProfileId
    isInteractiveServiceAvailable
    code
    name_ch
    name_en
  }
}"""

response = requests.post(
    url="https://info.cld.hkjc.com/graphql/base/",
    headers={"content-type": "application/json"},
    json={
        "query": body,
        "operationName": "teamList",
    },
)

print(len(response.json()["data"]["teamList"]))
