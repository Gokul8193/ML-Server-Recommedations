import pandas as pd
import os

input_dir = os.path.join(os.path.dirname(__file__), "input_params")

Estimated_Quality_score_df = pd.read_csv(os.path.join(input_dir, "estimated_quality_scores_1634725968.csv"))
Master_df = pd.read_csv(os.path.join(input_dir,'MASTER_CAMPAIGN_AD_GROUP_QUERY_results_1634725968.csv'))

# In[2]:

Estimated_Quality_score_df.info()
Master_df.info()

# In[3]:


list = Master_df['campaign_id'].unique()
len(list)

# In[4]:


Estimated_Quality_score_df.drop([ 'landing_page_experience', 'ad_relevance', 'expected_ctr',], axis=1, inplace=True)
Estimated_Quality_score_df

# In[5]:


list = Estimated_Quality_score_df['keyword'].unique()
len(list)

# In[6]:


Estimated_Quality_score_df['estimated_quality_score'] = Estimated_Quality_score_df['estimated_quality_score'].fillna(0)
Estimated_Quality_score_df

# In[7]:


Master_df

# In[8]:


# Merge Estimated_Quality_score_df and Master_df on 'campaign_id' and 'ad_group_id' and 'date' bringing in 'keyword','KW_types' and 'estimated_quality_score' as a new column
merged_df = pd.merge(Master_df, Estimated_Quality_score_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')
merged_df.rename(columns={'keyword': 'Keyword_Quality_Keyword', 'KW_types': 'Keyword_Quality_KW_types', 'estimated_quality_score': 'Keyword_Quality_Estimated_Quality_Score'}, inplace=True)
# Display the result
merged_df

# In[9]:


list = merged_df['campaign_id'].unique()
len(list)

# In[10]:


merged_df['Keyword_Quality_Keyword'].unique()

# In[11]:


list = merged_df['Keyword_Quality_Keyword'].unique()
len(list)

# In[12]:


positive_qs_df = merged_df[merged_df['Keyword_Quality_Estimated_Quality_Score'] <= 0]


# In[13]:


positive_qs_df

# In[14]:


conversion_rate_df = pd.read_csv(os.path.join(input_dir,'interaction_metrics_results_1634725968.csv'))
conversion_rate_df

# In[15]:


# Merge df1 and df2 on 'campaign_id' and 'ad_group_id' and 'date' bringing in 'keyword','KW_types' and 'estimated_quality_score' as a new column
merged_df2 = pd.merge(merged_df, conversion_rate_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')
merged_df2.rename(columns={'interactions': 'conversion_rate_Interactions', 'conversions': 'conversion_rate_Conversions', 'conversion_rate (%)': 'conversion_rate_Conversion_rate_(%)'}, inplace=True)

# Display the result
merged_df2

# In[16]:


ad_performance_df = pd.read_csv(os.path.join(input_dir,'ad_performance_metrics_results_1634725968.csv'))
ad_performance_df.rename(columns={
    'impressions': 'ad_performance_Impressions',
    'clicks': 'ad_performance_Clicks',
    'cost_usd': 'ad_performance_Cost_(USD)',
    'ctr': 'ad_performance_CTR',
    'average_cpc': 'ad_performance_Avg._CPC',
    'cost_per_acquisition': 'ad_performance_Cost_per_Acquisition',
    'interactions': 'ad_performance_Interactions',
    'conversions': 'ad_performance_Conversions',
    'conversion_rate (%)': 'ad_performance_Conversion_Rate_(%)',
    'search_absolute_top_impression_share': 'ad_performance_Search_Abs._Top_Impression_Share',
    'search_top_impression_share': 'ad_performance_Search_Top_Impression_Share',
    'search_impression_share': 'ad_performance_Search_Impression_Share',
    'search_rank_lost_impression_share': 'ad_performance_Search_Rank_Lost_Imp._Share'
}, inplace=True)

ad_performance_df

# In[17]:


ad_performance_df.drop(columns={'ad_group_name','campaign_name'}, inplace=True)

# In[18]:


merged_df3 = pd.merge(merged_df2, ad_performance_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')

# In[20]:


merged_df3.info()

# In[21]:


device_performance_df = pd.read_csv(os.path.join(input_dir,'device_performance_results_1634725968.csv'))
device_performance_df.rename(columns={
    'device': 'Device_performance_Device',
    'impressions': 'Device_performance_Impressions',
    'clicks': 'Device_performance_Clicks',
    'ctr': 'Device_performance_CTR',
    'cost_usd': 'Device_performance_Cost_USD',
    'conversions': 'Device_performance_Conversions',
    'cost_per_conversion': 'Device_performance_Cost_per_Conversion',
    'search_absolute_top_impression_share': 'Device_performance_Search_Abs_Top_Impression_Share',
    'search_budget_lost_absolute_top_impression_share': 'Device_performance_Search_Budget_Lost_Abs_Top_Impression_Share',
    'search_budget_lost_top_impression_share': 'Device_performance_Search_Budget_Lost_Top_Impression_Share',
    'search_top_impression_share': 'Device_performance_Search_Top_Impression_Share',
    'search_rank_lost_impression_share': 'Device_performance_Search_Rank_Lost_Impression_Share',
    'search_rank_lost_absolute_top_impression_share': 'Device_performance_Search_Rank_Lost_Abs_Top_Impression_Share',
    'search_rank_lost_top_impression_share': 'Device_performance_Search_Rank_Lost_Top_Impression_Share',
    'search_impression_share': 'Device_performance_Search_Impression_Share',
    'search_exact_match_impression_share': 'Device_performance_Search_Exact_Match_Impression_Share'
}, inplace=True)
device_performance_df.drop(columns={'campaign_name'}, inplace=True)
device_performance_df

# In[22]:


merged_df4 = pd.merge(merged_df3, device_performance_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')
merged_df4.info()

# In[23]:


keyword_performance_df = pd.read_csv(os.path.join(input_dir,'keyword_performance_results_1634725968.csv'))
keyword_performance_df.info()

# In[24]:


keyword_performance_df.drop(columns=['criterion_id'], inplace=True)

# In[25]:


keywords = keyword_performance_df['keyword_text'].unique()
len(keywords)

# In[26]:


keyword_performance_df.rename(columns={
    'keyword_text': 'Keyword_performance_Keyword_Text',
    'match_type': 'Keyword_performance_Keyword_Match_Type',
    'impressions': 'Keyword_performance_impressions',
    'clicks': 'Keyword_performance_clicks',
    'ctr': 'Keyword_performance_CTR',
    'average_cpc': 'Keyword_performance_average_cpc',
    'conversions': 'Keyword_performance_conversions',
    'cost_usd': 'Keyword_performance_cost_usd',
    'cost_per_conversion': 'Keyword_performance_cost_per_conversion',
    'search_impression_share': 'Keyword_performance_search_impression_share',
    'search_top_impression_share': 'Keyword_performance_search_top_impression_share',
    'search_absolute_top_impression_share': 'Keyword_performance_search_absolute_top_impression_share',
    'search_rank_lost_impression_share': 'Keyword_performance_search_rank_lost_impression_share',
    'absolute_top_impression_percentage': 'Keyword_performance_absolute_top_impression_percentage',
    'top_impression_percentage': 'Keyword_performance_top_impression_percentage',
    'estimated_first_position_cpc': 'Keyword_performance_estimated_first_position_cpc',
    'search_exact_match_impression_share': 'Keyword_performance_search_exact_match_impression_share'
}, inplace=True)
keyword_performance_df


# In[27]:


bid_adjustments_df =    pd.read_csv(os.path.join(input_dir,'bid_adjustments_results_1634725968.csv'))
bid_adjustments_df.drop(columns=['criterion_id'],inplace=True)

# In[28]:


bid_adjustments_df.rename(columns={
    'bid_modifier': 'bid_Adjustments_bid_modifier',
    'device_type': 'bid_Adjustments_device_type',
    'device_type_name': 'bid_Adjustments_device_type_name'}, inplace=True) 

# In[29]:


merged_df_keywords = pd.merge(keyword_performance_df, keyword_performance_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')

# In[30]:


merged_df5 = pd.merge(
    merged_df4,
    keyword_performance_df,
    how='outer',
    left_on=['campaign_id', 'ad_group_id', 'Date', 'Keyword_Quality_Keyword'],
    right_on=['campaign_id', 'ad_group_id', 'Date', 'Keyword_performance_Keyword_Text']
)
merged_df5.info()


# In[31]:


len(merged_df5['Keyword_performance_Keyword_Text'].unique())

# In[32]:


len(merged_df5['Keyword_Quality_Keyword'].unique())

# In[33]:


# Check rows where both keyword columns match exactly
matching_rows = merged_df5[
    merged_df5['Keyword_Quality_Keyword'] == merged_df5['Keyword_performance_Keyword_Text']
]
print(f"Number of matching keyword rows: {len(matching_rows)}")


# In[34]:


merged_df6 = pd.merge(merged_df5, bid_adjustments_df, on=['campaign_id','ad_group_id'], how='outer')
merged_df6.info()

# In[35]:


ad_schedule_df = pd.read_csv(os.path.join(input_dir,'ad_schedule_results_1634725968.csv'))
ad_schedule_df.info()

# In[36]:



ad_schedule_df.rename(columns={
    'start_hour': 'ad_schedule_start_hour',
    'end_hour': 'ad_schedule_end_hour',
    'day_pf_of_week': 'ad_schedule_day_of_week',
    'impressions': 'ad_schedule_impressions',
    'clicks': 'ad_schedule_clicks',
    'cost_usd': 'ad_schedule_cost_usd',
    'conversions': 'ad_schedule_conversions'},
inplace=True)
ad_schedule_df.info()

# In[37]:


merged_df7 = pd.merge(merged_df6, ad_schedule_df, on=['campaign_id', 'Date'], how='outer')
merged_df7.info()

# In[38]:


keywords_metadata_df = pd.read_csv(os.path.join(input_dir,'keyword_metadata_results_1634725968.csv'))
keywords_metadata_df.info()

# In[39]:


keywords_metadata_df.rename(columns={
    'keyword_text': 'keywords_meta_keyword_text',
    'match_type': 'keywords_meta_match_type',
    'quality_score': 'keywords_meta_quality_score'
  },
inplace=True)
keywords_metadata_df.info()

# In[40]:


len(merged_df7['Keyword_Quality_Keyword'].unique())

# In[41]:


len(keywords_metadata_df['keywords_meta_keyword_text'].unique())

# In[42]:


merged_df8 = pd.merge(merged_df7, keywords_metadata_df, 
            left_on=['campaign_id','ad_group_id', 'Date','Keyword_Quality_Keyword'],
            right_on=['campaign_id','ad_group_id', 'Date','keywords_meta_keyword_text'], how='outer')
merged_df8.info()

# In[43]:


search_terms_df = pd.read_csv(os.path.join(input_dir,'search_term_report_results_1634725968.csv'))
search_terms_df.info()

# In[44]:


search_terms_df.rename(columns={
    'search_term': 'search_term_search_term',
    'impressions': 'search_term_impressions',
    'clicks': 'search_term_clicks',
    'cost_usd' : 'search_term_cost_usd',
    'conversions': 'search_term_conversions'
  },
inplace=True)
search_terms_df.info()

# In[45]:


search_terms_df = search_terms_df.drop_duplicates('search_term_search_term')

# In[46]:


merged_df9 = pd.merge(merged_df8, search_terms_df, on=['campaign_id', 'ad_group_id', 'Date'], how='outer')
merged_df9.info()

# In[47]:


len(merged_df9['search_term_search_term'].unique())

# In[48]:


len(search_terms_df['search_term_search_term'].unique())

# In[49]:


geographic_report_df = pd.read_csv(os.path.join(input_dir,'geographic_report_results_1634725968.csv'))
geographic_report_df.head(5)

# In[50]:


geo_target_df = pd.read_csv(os.path.join(input_dir,'geo_target_constant_results_1634725968.csv'))   
geo_target_df.head(5)



# In[51]:


location_df = pd.read_csv(os.path.join(input_dir,'campaign_location_results_1634725968.csv'))
location_df.head(5)

# In[52]:


location_df['geo_target_constant'] = location_df['geo_target_constant'].str.extract(r'(\d+)')
len(location_df['geo_target_constant'].unique())

# In[53]:


location_df.head(5)

# In[54]:


location_df['geo_target_constant'] = location_df['geo_target_constant'].astype('int64')
location_df.head(5)


# In[55]:


len(location_df['geo_target_constant'].unique())

# In[56]:


location_merged = pd.merge(geographic_report_df, location_df, left_on=['campaign_id','country_criterion_id'], right_on=['campaign_id','geo_target_constant'], how='right')

# In[57]:


len(location_merged['geo_target_constant'].unique())

# In[58]:


location_merged.head(5)

# In[59]:


# Merge the two dataframes on the matching columns
merged_geographic_df = pd.merge(geographic_report_df, location_merged[['campaign_id','ad_group_id','Date','geo_target_constant']], left_on= ['campaign_id','ad_group_id','Date','country_criterion_id'], right_on=['campaign_id','ad_group_id','Date', 'geo_target_constant'], how='outer')
merged_geographic_df = merged_geographic_df.drop(columns=['campaign_name','country_criterion_id','location_type'])
merged_geographic_df.info()

# In[60]:


len(merged_geographic_df['geo_target_constant'].unique())

# In[61]:


merged_geographic_df.rename(columns={
    'impressions' : 'geographic_report_impressions',
    'clicks' : 'geographic_report_clicks',
    'ctr' : 'geographic_report_ctr',
    'cost_usd' : 'geographic_report_cost_usd',
    'conversions' : 'geographic_report_conversions',
    'cost_per_conversion' : 'geographic_report_cost_per_conversion',
    'geo_target_constant' : 'geographic_report_geo_target_constant'
},inplace=True)
merged_geographic_df.info()


# In[62]:


merged_df10 = pd.merge(merged_df9, merged_geographic_df, on=['campaign_id', 'ad_group_id', 'Date'], how='outer')   
merged_df10.info() 

# In[64]:


len(merged_df10['geographic_report_geo_target_constant'].unique())

# In[65]:


bidding_strategy_df = pd.read_csv(os.path.join(input_dir,'campaign_bidding_strategy_results_1634725968.csv')    )
bidding_strategy_df.drop(columns=['campaign_name'],inplace=True)
bidding_strategy_df.info()

# In[66]:


bidding_strategy_df.rename(columns={
    'bidding_strategy_type': 'bidding_strategy_bidding_strategy_type',
    'budget_amount_consumed': 'bidding_strategy_budget_amount_consumed',
    'target_roas': 'bidding_strategy_target_roas',
    'target_cpa': 'bidding_strategy_target_cpa_micros'
}, inplace=True)
bidding_strategy_df.info()

# In[67]:


merged_df11 = pd.merge(merged_df10, bidding_strategy_df, on=['campaign_id', 'ad_group_id','Date'], how='outer')
merged_df11.info()

# In[68]:


merged_df11.head(5)

# In[69]:


merged_df11.to_csv(os.path.join(input_dir,'merged_df11.csv'))

# In[70]:


import pandas as pd
loaded_df11 = pd.read_csv(os.path.join(input_dir,'merged_df11.csv'))
loaded_df11.drop(columns=['Unnamed: 0'], inplace=True)
loaded_df11.info()

# In[71]:


merged_df11 = loaded_df11

# In[72]:


negative_kw_df = pd.read_csv(os.path.join(input_dir,'campaign_negative_keywords_results_1634725968.csv'))
negative_kw_df.info()

# In[73]:


len(negative_kw_df['negative_keyword'].unique())

# In[74]:


# Keep only unique rows based on the 'negative_keyword' column
negative_kw_df_unique = negative_kw_df.drop_duplicates(subset=['negative_keyword'])

# Verify the number of unique 'negative_keyword' entries
unique_count = len(negative_kw_df_unique['negative_keyword'].unique())
print(unique_count)


# In[75]:


negative_kw_df_unique

# In[82]:


from builtins import list
neg_kw_map = negative_kw_df_unique.groupby('campaign_id')['negative_keyword'].agg(list).to_dict()
merged_df11['Negative_keywords'] = merged_df11['campaign_id'].map(neg_kw_map)



# In[83]:


merged_df11[['campaign_id','Negative_keywords']].iloc[50:100]

# In[84]:


merged_df12 = merged_df11

# In[86]:


merged_df12.count()

merged_df12.to_csv(os.path.join(input_dir,'merged_df12.csv'), index=False)
