def page_territory_deep_dive():
    """
    Detailed RTM drill-down.
    • Territory filter now includes “All”.
    • Map has no grey-blur or highlight layers – just coloured polygons
      wherever data exists.
    • Charts fill the Streamlit column via use_container_width=True.
    """

    import json, re, html
    from pathlib import Path
    import plotly.express as px
    import plotly.graph_objects as go

    # ───── CONSTANTS --------------------------------------------------------
    TEXT_CSV     = "all_brands_competitive_analysis_20250530_140609.csv"
    SUBCOUNTY_GJ = "kenya-subcounties-simplified.geojson"

    # ───── 1 ▸ competitor narrative CSV (cached) ---------------------------
    @st.cache_data(show_spinner="Loading competitor narrative …")
    def _load_comp_text():
        df = pd.read_csv(TEXT_CSV)
        df.columns = df.columns.str.strip()
        df[["Brand", "Competitor", "Territory"]] = df[
            ["Brand", "Competitor", "Territory"]
        ].apply(lambda s: s.astype(str).str.title().str.strip())
        return df

    COMP_TXT_DF = _load_comp_text()

    # ───── 2 ▸ sub-county GeoJSON (cached) ---------------------------------
    @st.cache_data(show_spinner="Loading sub-county shapes …")
    def _load_sub_geo():
        geo = json.loads(Path(SUBCOUNTY_GJ).read_text("utf-8"))
        for f in geo["features"]:
            name = (
                f["properties"].get("shapeName")
                or f["properties"].get("SubCounty")
                or f["properties"].get("Subcounty")
                or f["properties"].get("SUB_COUNTY")
                or f["properties"].get("NAME", "")
            ).title().strip()
            f["properties"]["SUB_KEY"] = name
        return geo

    SUBCOUNTY_GEO = _load_sub_geo()

    # ───── 3 ▸ HEADER & FILTER WIDGETS -------------------------------------
    st.markdown("## Territory Deep-Dive")

    c1, c2, c3 = st.columns([1, 1, 1])
    territory = c1.selectbox("Territory", ["All"] + sorted(GT_DF["Territory"].unique()))
    brand_list = ["All"] + sorted(GT_DF["Brand"].unique())
    default_brand_idx = brand_list.index("Ushindi Bar") if "Ushindi Bar" in brand_list else 0
    brand = c2.selectbox("Brand", brand_list, index=default_brand_idx)
    level_options = ["County", "Sub-County"]
    level = c3.selectbox(
        "Map granularity",
        level_options,
        index=level_options.index("Sub-County")) # default to Sub-County)

    # ───── 4 ▸ KPI CARDS ----------------------------------------------------
    view_df = GT_DF.copy()
    if territory != "All":
        view_df = view_df[view_df["Territory"] == territory]
    if brand != "All":
        view_df = view_df[view_df["Brand"] == brand]

    k1, k2, k3, k4 = st.columns(4)
    for box, title, value in zip(
        [k1, k2, k3, k4],
        ["Total Sales", "Market Share", "Competitor Strength", "White Space"],
        [
            f"{view_df[SALES].sum():,.0f}",
            f"{percent(view_df[CS]).mean():.1f}%",
            f"{percent(view_df[COMP]).mean():.1f}%",
            f"{view_df[WS].mean():.0f}",
        ],
    ):
        box.markdown(
            f'''<div class="kpiCardStyle"><h5>{title}</h5><p>{value}</p></div>''',
            unsafe_allow_html=True,
        )

    st.markdown("")  # spacer line

    # ───── 5 ▸ FILTER RTM ROWS --------------------------------------------
    rtm = RTM_DF.copy()
    if territory != "All":
        rtm = rtm[rtm["Territory"] == territory]
    if brand != "All":
        rtm = rtm[rtm["Brand"] == brand]

    # If no data, stop early with a message
    if rtm.empty:
        st.warning("No RTM rows for the current filter – nothing to plot.")
        return

    # ───── 6 ▸ BUILD MAP ----------------------------------------------------
    left, right = st.columns(2)

    

    with left:
        st.markdown("### RTM Hot-Zones")

        if level == "County":
            geo_src, id_field, key_col = COUNTY_GEO, "COUNTY_KEY", "County"
        else:
            # detect sub-county column automatically
            def _match(c): return "sub" in c.lower() and "county" in c.lower()
            key_col = next((c for c in rtm.columns if _match(c)), None)
            if key_col is None:
                st.error("❌ Sub-county column not found in RTM data.")
                st.stop()
            geo_src, id_field = SUBCOUNTY_GEO, "SUB_KEY"

        # full list of polygons to colour (Kenya map)
        all_keys = [f["properties"][id_field] for f in geo_src["features"]]

        map_df = (
            pd.DataFrame({id_field: all_keys})
            .merge(
                rtm[[key_col, AWS]].rename(columns={key_col: id_field}),
                how="left",
            )
            .fillna({AWS: 0})
        )

        mfig = px.choropleth_mapbox(
            map_df,
            geojson=geo_src,
            locations=id_field,
            featureidkey=f"properties.{id_field}",
            color=AWS,
            color_continuous_scale="YlOrRd",
            range_color=(0, 100),
            mapbox_style="carto-positron",
            center={"lat": 0.23, "lon": 37.9},
            zoom=5,
            opacity=0.9,
            height=520,
        )

        mfig.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(mfig, use_container_width=True)

    # ───── 7 ▸ AWS HISTOGRAM ----------------------------------------------
    with right:
        st.markdown("### AWS Score Distribution")

        aws_bins = [0, 20, 40, 60, 80, 100]
        aws_labels = ["0–20", "20–40", "40–60", "60–80", "80–100"]

        rtm["AWS_Bin"] = pd.cut(
        rtm[AWS],
        bins=aws_bins,
        labels=aws_labels,
        include_lowest=True,
        right=False)

        hist = px.histogram(
        rtm,
        x="AWS_Bin",
        color_discrete_sequence=["#38bdf8"],
        labels={"AWS_Bin": "AWS Score Bin"},
        category_orders={"AWS_Bin": aws_labels} )

        hist.update_layout(
        height=520,
        bargap=0.25,
        paper_bgcolor='#e3e8ef',
        plot_bgcolor='#e3e8ef',
        xaxis=dict(title="AWS Score", tickmode="array", tickvals=aws_labels),
        yaxis=AXIS,
        margin=dict(l=0, r=0, t=30, b=30),)



        mfig.update_layout( margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor="#e3e8ef")
        
        st.plotly_chart(hist, use_container_width=True)

    # ───── 8 ▸ COMPETITOR PANEL (only if a single territory & brand) -------
    if territory == "All" or brand == "All":
        return

    comp_rows = COMP_DF[
        (COMP_DF["Territory"] == territory) & (COMP_DF["BRAND"] == brand)
    ]
    if comp_rows.empty:
        st.info("No competitor data for this selection.")
        return

    sel_comp = st.selectbox(
        "Select Competitor", sorted(comp_rows["Competitor"].unique())
    )
    row = comp_rows[comp_rows["Competitor"] == sel_comp].iloc[0]
    cli, cmp = row["Pwani Market Share (%)"], row["Competitor Market Share (%)"]

    strip = go.Figure()
    strip.add_bar(
        y=["Market"], x=[cli], orientation="h",
        marker_color="#38bdf8", text=[f"Client {cli:.1f}%"], textposition="inside"
    )
    strip.add_bar(
        y=["Market"], x=[cmp], orientation="h",
        marker_color="#64748b", text=[f"{sel_comp} {cmp:.1f}%"], textposition="inside"
    )
    strip.update_layout(
        barmode="stack", height=140,
        title=f"Total Market Value: {cli+cmp:.1f}%",
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        font=dict(color="#000"), showlegend=False,
    )
    st.plotly_chart(strip, use_container_width=True)

    # narrative text cards
    bullets = re.compile(r"^\s*(?:-|\•|\d+\)|\d+\.)\s+(.*)$")

    def _card(text: str) -> str:
        paras, blt = [], []
        for ln in (text or "").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            m = bullets.match(ln)
            (blt if m else paras).append(html.escape(m.group(1) if m else ln))
        out = ["<div class='reason-card'>"]
        if paras:
            out.append("<p>" + " ".join(paras) + "</p>")
        if blt:
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in blt) + "</ul>")
        out.append("</div>")
        return "".join(out)

    st.markdown(
        """
        <style>
        .reason-card{border:1px solid #d4d4d8;border-radius:10px;padding:1rem 1.3rem;
                     margin:1rem 0;background:#f8fafc;color:#334155;font-size:.9rem;}
        .reason-card ul{margin:0 0 .2rem 1.1rem;padding-left:0;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    txt_rows = COMP_TXT_DF[
        (COMP_TXT_DF["Brand"] == brand)
        & (COMP_TXT_DF["Competitor"] == sel_comp)
        & (COMP_TXT_DF["Territory"] == territory)
    ]
    if txt_rows.empty:
        st.info("No narrative text for this competitor.")
    else:
        st.markdown("#### Reasons Outperformance")
        for _, r in txt_rows.iterrows():
            st.markdown(_card(r.get("Reasons_Outperformance") or r.get("Reason") or ""),
                        unsafe_allow_html=True)

    st.caption("Data sources: GT / RTM KPI · Kenya GeoJSONs · Competitor share & narrative files")
