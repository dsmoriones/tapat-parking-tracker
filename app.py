# SUB-TAB 3: 2026 WEEKLY ATTENDANCE TREND LINE (WITH ALL DATA LABELS)
                with tab_trend:
                    st.markdown("### 📈 2026 Year-to-Date Weekly Trend")
                    df["Total_Vehicles"] = (
                        df["Car_Count"] + df["Motorcycle_Count"]
                    )
                    trend_df = (
                        df
                        if selected_dash_loc == "All Locations"
                        else df[df["Location"] == selected_dash_loc]
                    )

                    trend_grouped = (
                        trend_df.groupby("Week_Number")[
                            ["Car_Count", "Motorcycle_Count", "Total_Vehicles"]
                        ]
                        .sum()
                        .reset_index()
                        .sort_values("Week_Number")
                    )

                    if not trend_grouped.empty:
                        fig_trend = go.Figure()

                        # Total Vehicles line with markers and text numbers
                        fig_trend.add_trace(
                            go.Scatter(
                                x=trend_grouped["Week_Number"],
                                y=trend_grouped["Total_Vehicles"],
                                mode="lines+markers+text",
                                name="Total Vehicles",
                                text=trend_grouped["Total_Vehicles"],
                                textposition="top center",
                                textfont=dict(color="#ffffff", size=11),
                                line=dict(color="#8b5cf6", width=3),
                                marker=dict(size=8),
                            )
                        )

                        # Cars line with markers and text numbers
                        fig_trend.add_trace(
                            go.Scatter(
                                x=trend_grouped["Week_Number"],
                                y=trend_grouped["Car_Count"],
                                mode="lines+markers+text",
                                name="Cars",
                                text=trend_grouped["Car_Count"],
                                textposition="top center",
                                textfont=dict(color="#60a5fa", size=10),
                                line=dict(color="#3b82f6", width=2, dash="dash"),
                                marker=dict(size=6),
                            )
                        )

                        # Motorcycles line with markers and text numbers
                        fig_trend.add_trace(
                            go.Scatter(
                                x=trend_grouped["Week_Number"],
                                y=trend_grouped["Motorcycle_Count"],
                                mode="lines+markers+text",
                                name="Motorcycles",
                                text=trend_grouped["Motorcycle_Count"],
                                textposition="bottom center",  # Offset slightly to prevent overlapping with cars
                                textfont=dict(color="#34d399", size=10),
                                line=dict(
                                    color="#10b981", width=2, dash="dash"
                                ),
                                marker=dict(size=6),
                            )
                        )

                        fig_trend.update_layout(
                            title=(
                                f"2026 Attendance Progression Across Weeks —"
                                f" {selected_dash_loc}"
                            ),
                            xaxis_title="Week Number",
                            yaxis_title="Total Vehicles Counted",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#f8fafc",
                            margin=dict(l=10, r=10, t=40, b=10),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.info("No historical logs available for 2026 yet.")
