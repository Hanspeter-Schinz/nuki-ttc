import streamlit as st
import altair as alt
import pandas as pd
import datetime

CSV_ENCODING:str = 'utf16'
CSV_SEP:str      = '\t'

KEY_DATE        = 'date'
KEY_TTVZ_MEMBER = 'name'
KEY_NUKI_ACTION = 'action'

def main() -> None:
    def show_preview(df_in:pd.DataFrame, st_in, num_show:int=10)->None:
        st_in.subheader(body=f'Preview newest {num_show} log entries')
        st_in.write(df_in.head(n=num_show))

    def filter_date_selection(df_in:pd.DataFrame, st_in) -> tuple[datetime.date, datetime.date, pd.DataFrame]:
        st_in.subheader(body='Filter Date Range')
        first_date, last_date = df_in[KEY_DATE].loc[[len(df_in)-1,0]]

        col_from, col_to = st_in.columns(spec=[1,1])
        DATE_FORMAT = 'YYYY-MM-DD'
        with col_from:
            from_date = st_in.date_input(label='From Date', value=first_date, format=DATE_FORMAT, help='select from date').isoformat()
        with col_to:
            # adding one day to tte to_date to have really all data of the given day otherwise eg. from 2025-01-31 to 2025-01-31 would be empty 
            to_date   = (st_in.date_input(label='To Date',   value=last_date,  format=DATE_FORMAT, help='select to date') + datetime.timedelta(days=1)).isoformat()
        df_in = df_in[(df_in[KEY_DATE] >= from_date) & (df_in[KEY_DATE] <= to_date)]
        return from_date, to_date, df_in
        #filtered_df = df

        # for now no additional filtering will be done
        #if False:
        #    st.subheader(body='Filter Specific Data')
        #    columns         = df.columns.tolist()
        #    columns.remove(KEY_DATE) # date is the main selector and already handled above
        #    selected_column = st.selectbox('Select Column to filter by', columns)
        #    unique_values   = df[selected_column].unique()
        #    selected_value  = st.selectbox('Select value', unique_values)
        #    filtered_df = df[df[selected_column] == selected_value]
        #return from_date, to_date, filtered_df

    def filter_more_selection(df_in:pd.DataFrame, st_in):
        st_in.subheader(body='Filter Specific Data')
        columns         = df_in.columns.tolist()
        columns.remove(KEY_DATE) # date is the main selector and already handled above
        selected_column = st_in.selectbox('Select Column to filter by', columns)
        unique_values   = df_in[selected_column].unique()
        selected_value  = st_in.selectbox('Select value', unique_values)
        df_in = df_in[df_in[selected_column] == selected_value]
        st.metric(label="Current Number Of Records:", value=len(df_in), help=f"Nunber of records in filter ('{selected_column}' == '{selected_value}')")
        st.write(df_in)

    st.set_page_config(page_title="Nuki Data Statistics", layout="wide", page_icon=":material/thumb_up:")
    st.title(body="Nuki Access Data", help='Statistical Infos for Nuki Access at Tischtennisgarage')
    
    uploaded_file = st.file_uploader(label="Upload your Nuki access data .csv file", type=["csv"], help='select a locally present correct nuki access log file')
    if uploaded_file is not None:
        df:pd.DataFrame = pd.read_csv(filepath_or_buffer=uploaded_file, sep=CSV_SEP, encoding=CSV_ENCODING)
        df = df[[KEY_DATE, KEY_TTVZ_MEMBER, KEY_NUKI_ACTION, 'trigger', 'state', 'autoUnlock']]
        # take trigger instead of empty name
        df[KEY_TTVZ_MEMBER] = df[KEY_TTVZ_MEMBER].fillna(value=df.trigger)

        show_preview(df_in=df, st_in=st)

        from_date, to_date, df = filter_date_selection(df_in=df, st_in=st)
        st.metric(label="Current Number Of Records:", value=len(df), help='Nunber of records in selected date range')
        st.write(df)

        filter_more_selection(df_in=df, st_in=st)
                
        GRAPH_FONT_SIZE:int = 15
        COLOR_X:str = 'red'
        COLOR_Y:str = 'green'     

        st.subheader(body=f'Nuki Access Statistics Chart Per Name From {from_date} To {to_date}')
        df_grouped_by_name = df.groupby(KEY_TTVZ_MEMBER, as_index=False).count() # we need index as normal column for alt.Chart()
        total_number_of_actions = sum(df_grouped_by_name[KEY_NUKI_ACTION])
        total_number_of_members = len(df_grouped_by_name)
        if st.button(label='Generate Name Bar Chart'):
            chart = alt.Chart(data=df_grouped_by_name[:]).mark_bar().encode(
                alt.X(shorthand=KEY_NUKI_ACTION
                    , title=f'Nuki Accesses: {total_number_of_actions}'
                    , axis=alt.Axis(labelColor=COLOR_X, labelFontSize=GRAPH_FONT_SIZE, titleColor=COLOR_X, titleFontSize=GRAPH_FONT_SIZE)
                ),
                alt.Y(shorthand=KEY_TTVZ_MEMBER
                    , sort='-x'
                    , title=f'TTVZ Members + Some Memberless Triggers: {total_number_of_members}'
                    , axis=alt.Axis(labelColor=COLOR_Y, labelFontSize=GRAPH_FONT_SIZE, titleColor=COLOR_Y, titleFontSize=GRAPH_FONT_SIZE, labelLimit=300)
                ),
                alt.Color(shorthand=KEY_NUKI_ACTION, type='nominal', legend=None), # different colors for given key without legend
            ).properties(
                height=alt.Step(30) # default 20
                )
            st.write(chart)

        st.subheader(body=f'Nuki Access Statistics Chart Per Date From {from_date} To {to_date}')
        TZ='Europe/Zurich' # need local timezone (Zurich) for dates
        # modifying df[KEY_DATE] to only have dates without times. Otherwise every date/time entry will be broken down to seconds level (we want day level)
        df[KEY_DATE] = pd.to_datetime(df[KEY_DATE], utc=True).map(lambda x: x.tz_convert(TZ)).dt.date.astype(str)
        df_grouped_by_date = df.groupby(by=df[KEY_DATE], group_keys=False, as_index=False).count()
        total_number_of_actions = sum(df_grouped_by_date[KEY_NUKI_ACTION])
        total_number_of_dates   = len(df_grouped_by_date)
        if st.button(label='Generate Date Bar Chart'):
            chart = alt.Chart(data=df_grouped_by_date[:]).mark_bar().encode(
                alt.X(shorthand=KEY_DATE
                    , title=f'Dates: {total_number_of_dates}'
                    , axis=alt.Axis(labelColor=COLOR_X, labelFontSize=GRAPH_FONT_SIZE, titleColor=COLOR_X, titleFontSize=GRAPH_FONT_SIZE)
                ),
                alt.Y(shorthand=KEY_NUKI_ACTION
                    , title=f'Nuki Accesses: {total_number_of_actions}'
                    , axis=alt.Axis(labelColor=COLOR_Y, labelFontSize=GRAPH_FONT_SIZE, titleColor=COLOR_Y, titleFontSize=GRAPH_FONT_SIZE)
                ),
                alt.Color(shorthand=KEY_NUKI_ACTION, type='nominal', legend=None), # different colors for given key without legend
            )
            st.write(chart)

if __name__ == "__main__":
    # run it via streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false
    main()    
# end main
