import json
import logging
import os
from datetime import datetime

import functions_framework
import requests

from gcp import storage
from gcp.logging import setup_logging

setup_logging()


@functions_framework.cloud_event
def main(_):
    storage.upload_json_to_bucket(
        data=get_hkjc_odds(odds_types=json.loads(os.environ["ODDS_TYPES"])),
        blob_name="odds.json",
        bucket_name=os.environ["BUCKET_NAME"],
        hive_partitioning={"_TIMESTAMP": get_current_timestamp()},
    )


def get_hkjc_odds(odds_types: list[str]) -> dict:
    logging.info(f"Getting HKJC data: {odds_types=}")
    body = """
      query matchList($startIndex: Int, $endIndex: Int,$startDate: String, $endDate: String, $matchIds: [String], $tournIds: [String], $fbOddsTypes: [FBOddsType]!, $fbOddsTypesM: [FBOddsType]!, $inplayOnly: Boolean, $featuredMatchesOnly: Boolean, $frontEndIds: [String], $earlySettlementOnly: Boolean, $showAllMatch: Boolean) {
        matches(startIndex: $startIndex,endIndex: $endIndex, startDate: $startDate, endDate: $endDate, matchIds: $matchIds, tournIds: $tournIds, fbOddsTypes: $fbOddsTypesM, inplayOnly: $inplayOnly, featuredMatchesOnly: $featuredMatchesOnly, frontEndIds: $frontEndIds, earlySettlementOnly: $earlySettlementOnly, showAllMatch: $showAllMatch) {
          id
          frontEndId
          matchDate
          kickOffTime
          status
          updateAt
          sequence
          esIndicatorEnabled
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
            id
            frontEndId
            nameProfileId
            isInteractiveServiceAvailable
            code
            name_en
            name_ch
          }
          isInteractiveServiceAvailable
          inplayDelay
          venue {
            code
            name_en
            name_ch
          }
          tvChannels {
            code
            name_en
            name_ch
          }
          liveEvents {
            id
            code
          }
          featureStartTime
          featureMatchSequence
          poolInfo {
            normalPools
            inplayPools
            sellingPools
            ntsInfo
            entInfo
          }
          runningResult {
            homeScore
            awayScore
            corner
          }
          runningResultExtra {
            homeScore
            awayScore
            corner
          }
          adminOperation {
            remark {
              typ
            }
          }
          foPools(fbOddsTypes: $fbOddsTypes) {
            id
            status
            oddsType
            instNo
            inplay
            name_ch
            name_en
            updateAt
            expectedSuspendDateTime
            lines {
              lineId
              status
              condition
              main
              combinations {
                combId
                str
                status
                offerEarlySettlement
                currentOdds
                selections {
                  selId
                  str
                  name_ch
                  name_en
                }
              }
            }
          }
        }
      }
      """
    response = requests.post(
        url="https://info.cld.hkjc.com/graphql/base/",
        headers={"content-type": "application/json"},
        json={
            "query": body,
            "variables": {
                "fbOddsTypes": odds_types,
                "fbOddsTypesM": odds_types,
                "showAllMatch": True,
            },
        },
        timeout=5,
    )
    response.raise_for_status()
    matches = response.json()["data"]["matches"]
    logging.info(f"Got HKJC data: {odds_types=}")
    return matches


def get_current_timestamp():
    return datetime.now().isoformat()
