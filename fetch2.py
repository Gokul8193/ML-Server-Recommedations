import argparse
import pandas as pd
import multiprocessing
import time
import os
from datetime import datetime, timedelta

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

STATUS_TO_NUM = {
    "BELOW_AVERAGE": 1,
    "AVERAGE": 2,
    "ABOVE_AVERAGE": 3,
    "UNSPECIFIED": None,
    "UNKNOWN": None
}

MAX_PROCESSES = multiprocessing.cpu_count()
BACKOFF_FACTOR = 5
MAX_RETRIES = 5

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "input_params")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -- GAQL Queries (ALL with placeholders for dates) --
MASTER_CAMPAIGN_AD_GROUP_QUERY = """
    SELECT 
        campaign.id,
        ad_group.id,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions,
        segments.date
    FROM 
        ad_group
    WHERE 
        segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

QUALITY_SCORE_QUERY = """
SELECT
  campaign.id,
  ad_group.id,
  ad_group_criterion.keyword.text,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.post_click_quality_score,
  ad_group_criterion.quality_info.search_predicted_ctr,
  ad_group_criterion.keyword.match_type,
  segments.date
FROM
  keyword_view
WHERE
     segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

INTERACTION_METRICS_QUERY = """
SELECT
  campaign.id,
  ad_group.id,
  metrics.interactions,
  metrics.conversions,
  segments.date
FROM 
    ad_group
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

AD_GROUP_PERFORMANCE_QUERY = """
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.cost_per_conversion,
  metrics.ctr,
  metrics.interactions,
  metrics.average_cpc,
  metrics.conversions,
  metrics.search_absolute_top_impression_share,
  metrics.search_top_impression_share,
  metrics.search_impression_share,
  metrics.search_rank_lost_impression_share,
  segments.date
FROM
  ad_group
WHERE
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

DEVICE_PERFORMANCE_QUERY = """
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  segments.device,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.cost_micros,
  metrics.conversions,
  metrics.cost_per_conversion,
  metrics.search_absolute_top_impression_share,
  metrics.search_budget_lost_absolute_top_impression_share,
  metrics.search_budget_lost_top_impression_share,
  metrics.search_top_impression_share,
  metrics.search_rank_lost_impression_share,
  metrics.search_rank_lost_absolute_top_impression_share,
  metrics.search_rank_lost_top_impression_share,
  metrics.search_impression_share,
  metrics.search_exact_match_impression_share,
  segments.date
FROM 
    ad_group
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

KEYWORD_PERFORMANCE_QUERY = """
SELECT
  campaign.id,
  ad_group.id,
  ad_group_criterion.criterion_id,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.average_cpc,
  metrics.conversions,
  metrics.cost_micros,
  metrics.cost_per_conversion,
  metrics.search_impression_share,
  metrics.search_top_impression_share, 
  metrics.search_absolute_top_impression_share,
  metrics.search_rank_lost_impression_share,
  metrics.absolute_top_impression_percentage,
  metrics.top_impression_percentage,
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  metrics.search_exact_match_impression_share,
  segments.date
FROM
  keyword_view
WHERE
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

BID_ADJUSTMENTS_QUERY = """
SELECT
    campaign.id,
    ad_group.id,
    ad_group_bid_modifier.bid_modifier,
    ad_group_bid_modifier.criterion_id,
    ad_group_bid_modifier.device.type
FROM ad_group_bid_modifier
"""

AD_SCHEDULE_QUERY = """
SELECT 
    campaign.id, 
    segments.date,
    ad_schedule_view.resource_name, 
    campaign_criterion.ad_schedule.start_hour, 
    campaign_criterion.ad_schedule.end_hour, 
    campaign_criterion.ad_schedule.day_of_week,
    metrics.impressions, 
    metrics.clicks, 
    metrics.cost_micros, 
    metrics.conversions
FROM ad_schedule_view
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

KEYWORD_METADATA_QUERY = """
SELECT
    campaign.id,
    ad_group.id,
    segments.date,
    ad_group_criterion.keyword.text,
    ad_group_criterion.keyword.match_type,
    ad_group_criterion.quality_info.quality_score
FROM 
    keyword_view
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

SEARCH_TERM_QUERY = """
SELECT
    campaign.id,
    ad_group.id,
    segments.date,
    search_term_view.search_term,
    metrics.impressions,
    metrics.clicks,
    metrics.cost_micros,
    metrics.conversions,
    metrics.cost_per_conversion
FROM
    search_term_view
WHERE
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

GEOGRAPHIC_REPORT_QUERY = """
SELECT
    campaign.id,
    ad_group.id,
    segments.date,
    geographic_view.country_criterion_id,
    geographic_view.location_type,
    metrics.impressions,
    metrics.clicks,
    metrics.ctr,
    metrics.cost_micros,
    metrics.conversions,
    metrics.cost_per_conversion
FROM
    geographic_view
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

GEO_TARGET_CONSTANT_QUERY = """
SELECT
    geo_target_constant.id,
    geo_target_constant.name,
    geo_target_constant.country_code,
    geo_target_constant.target_type
FROM
    geo_target_constant
"""

CAMPAIGN_BIDDING_STRATEGY_QUERY = """
SELECT 
  campaign.id, 
  campaign.name, 
  ad_group.id, 
  segments.date,
  campaign.bidding_strategy_type, 
  campaign.target_roas.target_roas, 
  campaign.target_cpa.target_cpa_micros 
FROM 
    ad_group
WHERE 
    segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

CAMPAIGN_LOCATION_QUERY = """
SELECT 
    campaign.id, 
    campaign_criterion.location.geo_target_constant, 
    campaign_criterion.type
FROM 
    campaign_criterion
WHERE 
    campaign_criterion.type = 'LOCATION'
"""

CAMPAIGN_NEGATIVE_KEYWORDS_QUERY = """
SELECT
  campaign.id,
  campaign_criterion.keyword.text
FROM 
  campaign_criterion
WHERE 
  campaign_criterion.negative = TRUE
  AND campaign_criterion.type = 'KEYWORD'
"""

AD_GROUP_AD_QUERY = """
SELECT
  ad_group.id,
  campaign.id,
  ad_group_ad.ad.id,
  ad_group_ad.ad.type,
  ad_group_ad.status,
  ad_group_ad.ad.final_urls,
  ad_group_ad.ad.name,
  ad_group_ad.ad.display_url, 
  ad_group_ad.ad.expanded_text_ad.headline_part1,
  ad_group_ad.ad.expanded_text_ad.headline_part2,
  ad_group_ad.ad.expanded_text_ad.headline_part3,
  ad_group_ad.ad.expanded_text_ad.description2,
  ad_group_ad.ad.expanded_text_ad.path1,
  ad_group_ad.ad.expanded_text_ad.path2,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.ad.responsive_search_ad.descriptions,
  ad_group_ad.ad.responsive_search_ad.path1,
  ad_group_ad.ad.responsive_search_ad.path2,
  segments.date,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions
FROM
  ad_group_ad
WHERE
      ad_group_ad.ad.type IN ('EXPANDED_TEXT_AD', 'RESPONSIVE_SEARCH_AD')
AND
      segments.date BETWEEN '{START_DATE}' AND '{END_DATE}'
"""

def estimate_quality_score(lp_exp, ad_rel, exp_ctr):
    lp = STATUS_TO_NUM.get(lp_exp.name, 0)
    ar = STATUS_TO_NUM.get(ad_rel.name, 0)
    ec = STATUS_TO_NUM.get(exp_ctr.name, 0)
    if None in (lp, ar, ec):
        return None
    return round(1 + 0.39 * lp + 0.22 * ar + 0.39 * ec, 2)

def collect_quality_scores(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService")
    results = []
    query = QUALITY_SCORE_QUERY.format(START_DATE=start_date, END_DATE=end_date)
    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                qi = row.ad_group_criterion.quality_info
                estimated_qs = estimate_quality_score(
                    qi.post_click_quality_score,
                    qi.creative_quality_score,
                    qi.search_predicted_ctr
                )
                results.append({
                    "campaign_id": row.campaign.id,
                    "ad_group_id": row.ad_group.id,
                    "Date": row.segments.date,
                    "keyword": row.ad_group_criterion.keyword.text,
                    "landing_page_experience": qi.post_click_quality_score.name,
                    "ad_relevance": qi.creative_quality_score.name,
                    "expected_ctr": qi.search_predicted_ctr.name,
                    "estimated_quality_score": estimated_qs,
                    "KW_types": row.ad_group_criterion.keyword.match_type
                })
        df = pd.DataFrame(results)
        file_name = os.path.join(OUTPUT_DIR, f"estimated_quality_scores_{customer_id}.csv")
        df.to_csv(file_name, index=False)
        print(f"✅ Quality scores saved: {file_name}")
    except GoogleAdsException as ex:
        print(f"❌ Quality score request failed for {customer_id} with ID: {ex.request_id}")
        for error in ex.failure.errors:
            print(f"\tError: {error.message}")

def issue_search_request(client, customer_id, query, query_name, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService")
    retry_count = 0
    query_formatted = query.format(START_DATE=start_date, END_DATE=end_date)
    while True:
        try:
            stream = ga_service.search_stream(customer_id=customer_id, query=query_formatted)
            result_data = []
            for batch in stream:
                for row in batch.results:
                    qi = row.ad_group_criterion.quality_info
                estimated_qs = estimate_quality_score(
                    qi.post_click_quality_score,
                    qi.creative_quality_score,
                    qi.search_predicted_ctr
                )
                results.append({
                    "campaign_id": row.campaign.id,
                    "ad_group_id": row.ad_group.id,
                    "Date": row.segments.date,
                    "keyword": row.ad_group_criterion.keyword.text,
                    "landing_page_experience": qi.post_click_quality_score.name,
                    "ad_relevance": qi.creative_quality_score.name,
                    "expected_ctr": qi.search_predicted_ctr.name,
                    "estimated_quality_score": estimated_qs,
                    "KW_types": row.ad_group_criterion.keyword.match_type
                })
        
        
        

        df = pd.DataFrame(results)
        file_name = os.path.join(OUTPUT_DIR, f"estimated_quality_scores_{customer_id}.csv")
        df.to_csv(file_name, index=False)
        print(f"✅ Quality scores saved: {file_name}")

    except GoogleAdsException as ex:
        print(f"❌ Quality score request failed for {customer_id} with ID: {ex.request_id}")
        for error in ex.failure.errors:
            print(f"\tError: {error.message}")

def issue_search_request(client, customer_id, query, query_name):
    ga_service = client.get_service("GoogleAdsService")
    retry_count = 0

    while True:
        try:
            stream = ga_service.search_stream(customer_id=customer_id, query=query)
            result_data = []

            for batch in stream:
                for row in batch.results:
                    if query_name == "interaction_metrics":
                        interactions = row.metrics.interactions
                        conversions = row.metrics.conversions
                        conversion_rate = (conversions / interactions) * 100 if interactions > 0 else 0.0
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "interactions": interactions,
                            "conversions": conversions,
                            "conversion_rate (%)": round(conversion_rate, 2)
                        }
                    
                    elif query_name == "MASTER_CAMPAIGN_AD_GROUP_QUERY":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "ctr": row.metrics.ctr,
                            "average_cpc_usd": row.metrics.average_cpc / 1_000_000,

                        }

                    elif query_name == "ad_performance_metrics":
                        interactions = row.metrics.interactions
                        conversions = row.metrics.conversions
                        conversion_rate = (conversions / interactions) * 100 if interactions > 0 else 0.0
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "campaign_name": row.campaign.name,
                            "ad_group_name": row.ad_group.name,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,                           
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "ctr": row.metrics.ctr,
                            "average_cpc": row.metrics.average_cpc,
                            "cost_per_acquisition": row.metrics.cost_per_conversion,
                            "interactions": interactions,
                            "conversions": conversions,
                            "conversion_rate (%)": round(conversion_rate, 2),
                            "search_absolute_top_impression_share": row.metrics.search_absolute_top_impression_share,
                            "search_top_impression_share": row.metrics.search_top_impression_share,
                            "search_impression_share": row.metrics.search_impression_share,
                            "search_rank_lost_impression_share": row.metrics.search_rank_lost_impression_share,
                        }


                    elif query_name == "device_performance":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "campaign_name": row.campaign.name,
                            "device": row.segments.device.name,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "ctr": row.metrics.ctr,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "conversions": row.metrics.conversions,
                            "cost_per_conversion": row.metrics.cost_per_conversion,
                            # "search_budget_lost_impression_share": row.metrics.search_budget_lost_impression_share,
                            "search_absolute_top_impression_share": row.metrics.search_absolute_top_impression_share,
                            "search_budget_lost_absolute_top_impression_share": row.metrics.search_budget_lost_absolute_top_impression_share,
                            "search_budget_lost_top_impression_share": row.metrics.search_budget_lost_top_impression_share,
                            "search_top_impression_share": row.metrics.search_top_impression_share,
                            "search_rank_lost_impression_share": row.metrics.search_rank_lost_impression_share,
                            "search_rank_lost_absolute_top_impression_share": row.metrics.search_rank_lost_absolute_top_impression_share,
                            "search_rank_lost_top_impression_share": row.metrics.search_rank_lost_top_impression_share,
                            "search_impression_share": row.metrics.search_impression_share,
                            "search_exact_match_impression_share": row.metrics.search_exact_match_impression_share
                        }
                    elif query_name == "keyword_performance":
                        average_cpc = row.metrics.average_cpc if row.metrics.average_cpc else 0.0
                        abs_top_impr_share = row.metrics.search_absolute_top_impression_share if row.metrics.search_absolute_top_impression_share else 0.0
                        estimated_first_pos_cpc = round(average_cpc * abs_top_impr_share,2)
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "criterion_id": row.ad_group_criterion.criterion_id,
                            # Where Not added
                            "keyword_text": row.ad_group_criterion.keyword.text,
                            "match_type": row.ad_group_criterion.keyword.match_type.name,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "ctr": row.metrics.ctr,
                            "average_cpc": row.metrics.average_cpc,
                            "conversions": row.metrics.conversions,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "cost_per_conversion": row.metrics.cost_per_conversion,
                            "search_impression_share": row.metrics.search_impression_share,
                            "search_top_impression_share": row.metrics.search_top_impression_share,
                            "search_absolute_top_impression_share": row.metrics.search_absolute_top_impression_share,
                            "search_rank_lost_impression_share": row.metrics.search_rank_lost_impression_share,
                            "absolute_top_impression_percentage": row.metrics.absolute_top_impression_percentage,
                            "top_impression_percentage": row.metrics.top_impression_percentage,
                            "estimated_first_position_cpc": estimated_first_pos_cpc,
                            "search_exact_match_impression_share": row.metrics.search_exact_match_impression_share
                        }
                    elif query_name == "ad_schedule":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "Date": row.segments.date,
                            "resource_name": row.ad_schedule_view.resource_name,
                            "start_hour": row.campaign_criterion.ad_schedule.start_hour,
                            "end_hour": row.campaign_criterion.ad_schedule.end_hour,
                            "day_of_week": row.campaign_criterion.ad_schedule.day_of_week.name,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "cost_usd": row.metrics.cost_micros/ 1_000_000,
                            "conversions": row.metrics.conversions
                            
                        }

                    elif query_name == "keyword_metadata":
                       row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "keyword_text": row.ad_group_criterion.keyword.text,
                            "match_type": row.ad_group_criterion.keyword.match_type.name,
                            "quality_score": row.ad_group_criterion.quality_info.quality_score
                       }
                    elif query_name == "search_term_report":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "search_term": row.search_term_view.search_term,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "conversions": row.metrics.conversions,
                            
                       }
                    
                    elif query_name == "geographic_report":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "Date": row.segments.date,
                            "campaign_name": row.campaign.name,
                            "country_criterion_id": row.geographic_view.country_criterion_id,
                            "location_type": row.geographic_view.location_type.name,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "ctr": row.metrics.ctr,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "conversions": row.metrics.conversions,
                            "cost_per_conversion": row.metrics.cost_per_conversion
                       }
                    elif query_name == "geo_target_constant":
                        row_data = {
                            "geo_target_constant_id": row.geo_target_constant.id,
                            "country_name": row.geo_target_constant.name,
                            "country_code": row.geo_target_constant.country_code,
                            "target_type": row.geo_target_constant.target_type
                        }
                    elif query_name == "campaign_bidding_strategy":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "campaign_name": row.campaign.name,
                            "ad_group_id" : row.ad_group.id,
                            "Date": row.segments.date,
                            "bidding_strategy_type": row.campaign.bidding_strategy_type.name,
                            "budget_amount_consumed": round(row.campaign_budget.amount_micros / 1_000_000, 2) if row.campaign_budget and row.campaign_budget.amount_micros else None,
                            "target_roas": row.campaign.target_roas.target_roas if row.campaign.target_roas else None,
                            "target_cpa": round(row.campaign.target_cpa.target_cpa_micros / 1_000_000, 2) if row.campaign.target_cpa and row.campaign.target_cpa.target_cpa_micros else None
                       }
                    elif query_name == "campaign_location":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "geo_target_constant": row.campaign_criterion.location.geo_target_constant,
                            "criterion_type": row.campaign_criterion.type.name if row.campaign_criterion.type else None
                       }

                    elif query_name == "campaign_negative_keywords":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "negative_keyword": row.campaign_criterion.keyword.text
                        }
                    # elif query_name == "user_list":
                    #     row_data = {
                    #         "campaign_id": row.campaign.id,
                    #         "ad_group_id": row.ad_group.id,
                    #         "user_list": row.ad_group_criterion.user_list.user_list
                    #     }

                    elif query_name == "ad_group_ad":
                        row_data = {
                            "ad_group_id": row.ad_group.id,
                            "campaign_id": row.campaign.id,
                            "Date": row.segments.date,
                            "ad_id": row.ad_group_ad.ad.id,
                            "ad_type": row.ad_group_ad.ad.type.name,
                            "ad_status": row.ad_group_ad.status.name,
                            "final_urls": list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else None,
                            "ad_name": row.ad_group_ad.ad.name,
                            "display_url": row.ad_group_ad.ad.display_url,
                            "headline_part1": row.ad_group_ad.ad.expanded_text_ad.headline_part1,
                            "headline_part2": row.ad_group_ad.ad.expanded_text_ad.headline_part2,
                            "headline_part3": row.ad_group_ad.ad.expanded_text_ad.headline_part3,
                            "description2": row.ad_group_ad.ad.expanded_text_ad.description2,
                            "path1": row.ad_group_ad.ad.expanded_text_ad.path1,
                            "path2": row.ad_group_ad.ad.expanded_text_ad.path2,
                            "responsive_search_ad_headlines": [headline.text for headline in row.ad_group_ad.ad.responsive_search_ad.headlines] if row.ad_group_ad.ad.responsive_search_ad else None,
                            "responsive_search_ad_descriptions": [description.text for description in row.ad_group_ad.ad.responsive_search_ad.descriptions] if row.ad_group_ad.ad.responsive_search_ad else None,
                            "responsive_search_ad_path1": row.ad_group_ad.ad.responsive_search_ad.path1 if row.ad_group_ad.ad.responsive_search_ad else None,
                            "responsive_search_ad_path2": row.ad_group_ad.ad.responsive_search_ad.path2 if row.ad_group_ad.ad.responsive_search_ad else None,
                            "impressions": row.metrics.impressions,
                            "clicks": row.metrics.clicks,
                            "cost_usd": row.metrics.cost_micros / 1_000_000,
                            "conversions": row.metrics.conversions
                        }
                    elif query_name == "bid_adjustments":
                        row_data = {
                            "campaign_id": row.campaign.id,
                            "ad_group_id": row.ad_group.id,
                            "bid_modifier": row.ad_group_bid_modifier.bid_modifier,
                            "device_type": row.ad_group_bid_modifier.device.type,
                            "device_type_name": row.ad_group_bid_modifier.device.type.name if row.ad_group_bid_modifier.device else None,
                            "criterion_id": row.ad_group_bid_modifier.criterion_id
                        }

                    result_data.append(row_data)

            return (True, {"results": result_data})

        except GoogleAdsException as ex:
            if retry_count < MAX_RETRIES:
                retry_count += 1
                time.sleep(retry_count * BACKOFF_FACTOR)
            else:
                return (
                    False,
                    {"exception": ex, "customer_id": customer_id, "query": query},
                )

def collect_metrics(client, customer_ids, start_date, end_date):
    queries = [
        ("MASTER_CAMPAIGN_AD_GROUP_QUERY", MASTER_CAMPAIGN_AD_GROUP_QUERY),
        ("interaction_metrics", INTERACTION_METRICS_QUERY),
        ("ad_performance_metrics", AD_GROUP_PERFORMANCE_QUERY),
        ("device_performance", DEVICE_PERFORMANCE_QUERY),
        ("keyword_performance", KEYWORD_PERFORMANCE_QUERY),
        ("ad_schedule", AD_SCHEDULE_QUERY),
        ("keyword_metadata", KEYWORD_METADATA_QUERY),
        ("search_term_report", SEARCH_TERM_QUERY),
        ("geographic_report", GEOGRAPHIC_REPORT_QUERY),
        ("campaign_bidding_strategy", CAMPAIGN_BIDDING_STRATEGY_QUERY),
        ("campaign_location", CAMPAIGN_LOCATION_QUERY),
        ("campaign_negative_keywords", CAMPAIGN_NEGATIVE_KEYWORDS_QUERY),
        # ("user_list", USER_LIST_QUERY),
        ("ad_group_ad", AD_GROUP_AD_QUERY),
        ("bid_adjustments", BID_ADJUSTMENTS_QUERY),
        ("geo_target_constant", GEO_TARGET_CONSTANT_QUERY)  
    ]
    inputs = [(client, cid, q, name, start_date, end_date) for cid in customer_ids for name, q in queries]
    with multiprocessing.Pool(MAX_PROCESSES) as pool:
        results = pool.starmap(issue_search_request, inputs)
    for idx, res in enumerate(results):
        query_name = inputs[idx][3]
        customer_id = inputs[idx][1]
        if res[0]:
            df = pd.DataFrame(res[1]["results"])
            file_name = os.path.join(OUTPUT_DIR, f"{query_name}_results_{customer_id}.csv")
            df.to_csv(file_name, index=False)
            print(f"{query_name} saved: {file_name}")
        else:
            ex = res[1]["exception"]
            print(f"Failed: {query_name} for customer {customer_id} | Request ID: {ex.request_id}")
            for error in ex.failure.errors:
                print(f"\tError: {error.message}")

def main(client, customer_ids, start_date, end_date):
    print("🔍 Collecting Estimated Quality Scores...")
    for cid in customer_ids:
        collect_quality_scores(client, cid, start_date, end_date)
    print("Collecting Campaign & Ad Group Metrics...")
    collect_metrics(client, customer_ids, start_date, end_date)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Google Ads data for reporting.")
    parser.add_argument("-c", "--customer_ids", nargs="+", required=True, help="Google Ads customer IDs")
    parser.add_argument("-l", "--login_customer_id", type=str, help="Login customer ID (for MCC)")
    parser.add_argument("-d", "--days", type=int, default=30, help="Number of days for the report (default: 30)")
    args = parser.parse_args()
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=args.days)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    client = GoogleAdsClient.load_from_storage('/home/minorilabs/Desktop/Google ads Client/google-ads-python/google-ads.yaml')
    if args.login_customer_id:
        client.login_customer_id = args.login_customer_id
    main(client, args.customer_ids, start_date_str, end_date_str)
