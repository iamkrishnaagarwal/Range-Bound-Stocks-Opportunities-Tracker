def finder(filtered_df):
    opportunities_list = []
    total_opportunities = 0

    for i in range(filtered_df.shape[0]):
        # Construct the URL for fetching candle data
        url = f'https://api.upstox.com/v2/historical-candle/intraday/{filtered_df["instrument_key"][i]}/1minute'
        headers = {'Accept': 'application/json'}

        # Fetch the candle data
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        candles_data = response.json().get('data', {}).get('candles', [])

        if candles_data:
            # Create a DataFrame from the candle data
            df = pd.DataFrame(candles_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            df.drop(columns=['OI'], inplace=True)
            df['Price Range %'] = ((df['High'] - df['Low']) / df['Low']) * 100

            # Filter for opportunities where Price Range % is greater than or equal to 0.5%
            filtered_df_opp = df[df['Price Range %'] >= 0.5].copy()

            if not filtered_df_opp.empty:
                # Process the filtered opportunities
                filtered_df_opp['Timestamp'] = pd.to_datetime(filtered_df_opp['Timestamp'])
                filtered_df_opp.sort_values(by='Timestamp', ascending=False, inplace=True)
                opportunities_count = filtered_df_opp.shape[0]
                total_opportunities += opportunities_count

                opportunity_data = {
                    'tradingsymbol': filtered_df["tradingsymbol"][i],
                    'opportunities_count': opportunities_count,
                    'details': filtered_df_opp
                }
                opportunities_list.append(opportunity_data)

                # Calculate the average Price Range % of the last 20% of opportunities
                num_opportunities = len(filtered_df_opp)
                last_20_percent_index = max(1, int(num_opportunities * 0.2))
                last_20_percent_opportunities = filtered_df_opp.head(last_20_percent_index)
                opportunities_list = sorted(opportunities_list, key=lambda x: x['details']['Timestamp'].max(), reverse=True)
                st.write(opportunities_list)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.code(filtered_df['tradingsymbol'][i])

                with col2:         
                    if not last_20_percent_opportunities.empty:
                        avg_price_range_last_20_percent = last_20_percent_opportunities['Price Range %'].mean()
                        st.write(f"Average Price Range: {avg_price_range_last_20_percent:.2f}%")
                
                with col3:
                    # Print the latest opportunity time
                    latest_opportunity_time = filtered_df_opp['Timestamp'].max()
                    st.write(f"Latest opportunity: {latest_opportunity_time}")

                with col4:
                    st.write(f"Total opportunities: {total_opportunities}")
