import logging
import os
from datetime import datetime, timedelta

import functions_framework
import pytz
import requests

from gcp import storage
from gcp.logging import setup_logging

setup_logging()


@functions_framework.cloud_event
def main(_):
    date = get_yesterday()

    storage.upload_json_to_bucket(
        date=date,
        blob_name="results.json",
        bucket_name=os.environ["BUCKET_NAME"],
        hive_partitioning={"_DATE": date},
    )


def get_hkjc_result(date: str) -> list[dict]:
    PAGE_SIZE = 20
    page = 1
    results = []

    body = """
    query matchResults($startDate: String, $endDate: String, $startIndex: Int,$endIndex: Int,$teamId: String) {
      timeOffset {
        fb
      }
      matchNumByDate(startDate: $startDate, endDate: $endDate, teamId: $teamId) {
        total
      }
      matches: matchResult(startDate: $startDate, endDate: $endDate, startIndex: $startIndex,endIndex: $endIndex, teamId: $teamId) {
        id
        status
        frontEndId
        matchDayOfWeek
        matchNumber
        matchDate
        kickOffTime
        sequence
        homeTeam {
          id
          name_en
          name_ch
        }
        awayTeam {
          id
          name_en
          name_ch
        }
        tournament {
          code
          name_en
          name_ch      
        }
        results {
          homeResult
          awayResult
          resultConfirmType
          payoutConfirmed
          stageId
          resultType
          sequence
        }
        poolInfo {
          payoutRefundPools
          refundPools
          ntsInfo
          entInfo
        }
      }
    }
  """
    while True:
        logging.info(f"Getting HKJC result: {date=}, {page=}")

        response = requests.post(
            url="https://info.cld.hkjc.com/graphql/base/",
            headers={"content-type": "application/json"},
            json={
                "query": body,
                "variables": {
                    "startDate": date,
                    "endDate": date,
                    "startIndex": (page - 1) * PAGE_SIZE + 1,
                    "endIndex": page * PAGE_SIZE,
                },
            },
        )
        response.raise_for_status()
        data = response.json()["data"]
        results.extend(data["matches"])

        logging.info(f"Got HKJC result: {date=}, {page=}")

        if len(results) == data["matchNumByDate"]["total"]:
            return results

        page += 1


def get_yesterday():
    yesterday = datetime.now(tz=pytz.timezone("Hongkong")) - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")
