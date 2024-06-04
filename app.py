## Cognos report analyser
# Get report name, package name, model name, page details, datasource detail, calcs

import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

def parse_model_path(model_path):
    """
    Function to parse model path and extract package name and model name separately.
    """
    package_start_index = model_path.find("@name='") + len("@name='")
    package_end_index = model_path.find("'", package_start_index)
    package_name = model_path[package_start_index:package_end_index]
    
    model_start_index = model_path.find("@name='", package_end_index) + len("@name='")
    model_end_index = model_path.find("'", model_start_index)
    model_name = model_path[model_start_index:model_end_index]
    
    return package_name, model_name

def parse_cognos_report(xml_content):
    root = ET.fromstring(xml_content)
    namespace = {'c': 'http://developer.cognos.com/schemas/report/16.2/'}
    
    report_name = root.find('c:reportName', namespace).text
    pages = root.findall('.//c:reportPages/c:page', namespace)
    num_pages = len(pages)
    
    model_path_element = root.find('c:modelPath', namespace)
    model_path = model_path_element.text if model_path_element is not None else 'No model path found'
    
    package_name, model_name = parse_model_path(model_path)
    
    queries = root.findall('.//c:queries/c:query', namespace)
    datasource_details = []
    
    for query in queries:
        query_name = query.get('name')
        columns = []
        detail_filters = []
        data_items = query.findall('.//c:selection/c:dataItem', namespace)
        
        for data_item in data_items:
            column_name = data_item.get('name')
            expression = data_item.find('c:expression', namespace).text
            rollup_aggregate = data_item.get('rollupAggregate', 'none')
            aggregate = data_item.get('aggregate', 'none')
            item_details = {
                'name': column_name,
                'expression': expression,
                'rollupAggregate': rollup_aggregate,
                'aggregate': aggregate
            }
            columns.append(item_details)
        
        detail_filters_nodes = query.findall('.//c:detailFilters/c:detailFilter', namespace)
        for filter_node in detail_filters_nodes:
            filter_expression = filter_node.find('c:filterExpression', namespace).text
            detail_filters.append({'expression': filter_expression})
        
        datasource_details.append({
            'query_name': query_name,
            'columns': columns,
            'detail_filters': detail_filters
        })
    
    page_details = []
    
    for page in pages:
        page_name = page.get('name')
        page_content = []
        
        lists = page.findall('.//c:list', namespace)
        for lst in lists:
            list_name = lst.get('name')
            ref_query = lst.get('refQuery')
            columns = []
            data_items = lst.findall('.//c:listColumnBody/c:contents/c:textItem/c:dataSource/c:dataItemValue', namespace)
            for data_item in data_items:
                columns.append(data_item.get('refDataItem'))
            page_content.append({
                'list_name': list_name,
                'ref_query': ref_query,
                'columns': columns
            })
        
        page_details.append({
            'page_name': page_name,
            'content': page_content
        })
    
    return report_name, num_pages, package_name, model_name, datasource_details, page_details

st.title("Cognos Accelerator")

uploaded_file = st.file_uploader("Upload Cognos Report XML (in .txt format)", type="txt")

if uploaded_file is not None:
    xml_content = uploaded_file.read().decode("utf-8")
    
    report_name, num_pages, package_name, model_name, datasource_details, page_details = parse_cognos_report(xml_content)
    
    st.header("Report Details")
    st.write(f"**Report Name:** {report_name}")
    st.write(f"**Number of Pages:** {num_pages}")
    st.write(f"**Package Name:** {package_name}")
    st.write(f"**Model Name:** {model_name}")
    
    st.header("Datasource Details")
    for datasource in datasource_details:
        st.subheader(f"Query Name: {datasource['query_name']}")
        
        if datasource['columns']:
            st.write("**Columns:**")
            columns_df = pd.DataFrame(datasource['columns'])
            st.table(columns_df)
        
        if datasource['detail_filters']:
            st.write("**Detail Filters:**")
            filters_df = pd.DataFrame(datasource['detail_filters'])
            st.table(filters_df)
    
    st.header("Page Details")
    for page in page_details:
        st.subheader(f"Page Name: {page['page_name']}")
        
        for content in page['content']:
            st.write(f"**Referenced Query:** {content['ref_query']}")
            if content['columns']:
                st.write("**Columns in the List:**")
                columns_df = pd.DataFrame(content['columns'], columns=['Column Name'])
                st.table(columns_df)
else:
    st.info("Please upload a Cognos report XML file in .txt format.")
