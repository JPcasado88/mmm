from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from ..models.models import DailyMarketingData, ExternalFactor

class MetricsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview_metrics(self, start_date: str, end_date: str) -> Dict:
        """Get high-level metrics for dashboard overview"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get current period metrics
        current_metrics = self._get_period_metrics(start, end)
        
        # Get previous period for comparison
        period_length = (end - start).days
        prev_start = start - timedelta(days=period_length)
        prev_end = start - timedelta(days=1)
        previous_metrics = self._get_period_metrics(prev_start, prev_end)
        
        # Calculate period-over-period changes
        spend_change = self._calculate_change(previous_metrics['total_spend'], current_metrics['total_spend'])
        revenue_change = self._calculate_change(previous_metrics['total_revenue'], current_metrics['total_revenue'])
        roas_change = self._calculate_change(previous_metrics['roas'], current_metrics['roas'])
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'total_spend': current_metrics['total_spend'],
            'total_revenue': current_metrics['total_revenue'],
            'roas': current_metrics['roas'],
            'total_conversions': current_metrics['total_conversions'],
            'channels': current_metrics['channels'],
            'period_comparison': {
                'spend_change': spend_change,
                'revenue_change': revenue_change,
                'roas_change': roas_change
            }
        }
    
    def _get_period_metrics(self, start: datetime, end: datetime) -> Dict:
        """Get metrics for a specific period"""
        # Query aggregated metrics
        results = self.db.query(
            DailyMarketingData.channel,
            func.sum(DailyMarketingData.spend).label('spend'),
            func.sum(DailyMarketingData.revenue).label('revenue'),
            func.sum(DailyMarketingData.conversions).label('conversions'),
            func.sum(DailyMarketingData.clicks).label('clicks'),
            func.sum(DailyMarketingData.impressions).label('impressions')
        ).filter(
            and_(
                DailyMarketingData.date >= start,
                DailyMarketingData.date <= end
            )
        ).group_by(DailyMarketingData.channel).all()
        
        channels = []
        total_spend = 0
        total_revenue = 0
        total_conversions = 0
        
        for row in results:
            spend = float(row.spend or 0)
            revenue = float(row.revenue or 0)
            conversions = int(row.conversions or 0)
            roas = revenue / spend if spend > 0 else 0
            
            channels.append({
                'name': row.channel,
                'spend': round(spend, 2),
                'revenue': round(revenue, 2),
                'conversions': conversions,
                'roas': round(roas, 2),
                'clicks': int(row.clicks or 0),
                'impressions': int(row.impressions or 0)
            })
            
            total_spend += spend
            total_revenue += revenue
            total_conversions += conversions
        
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0
        
        return {
            'total_spend': round(total_spend, 2),
            'total_revenue': round(total_revenue, 2),
            'total_conversions': total_conversions,
            'roas': round(overall_roas, 2),
            'channels': channels
        }
    
    def _calculate_change(self, previous: float, current: float) -> Dict:
        """Calculate period-over-period change"""
        if previous == 0:
            return {'value': 0, 'percentage': 0}
        
        absolute_change = current - previous
        percentage_change = (absolute_change / previous) * 100
        
        return {
            'value': round(absolute_change, 2),
            'percentage': round(percentage_change, 2)
        }
    
    def get_channel_performance(self, channel: str, start_date: str, end_date: str) -> Dict:
        """Get detailed performance metrics for a specific channel"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get daily data for the channel
        daily_data = self.db.query(DailyMarketingData).filter(
            and_(
                DailyMarketingData.channel == channel,
                DailyMarketingData.date >= start,
                DailyMarketingData.date <= end
            )
        ).order_by(DailyMarketingData.date).all()
        
        if not daily_data:
            return {'error': f'No data found for channel: {channel}'}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([{
            'date': d.date,
            'spend': float(d.spend),
            'revenue': float(d.revenue),
            'conversions': d.conversions,
            'clicks': d.clicks,
            'impressions': d.impressions
        } for d in daily_data])
        
        # Calculate metrics
        total_spend = df['spend'].sum()
        total_revenue = df['revenue'].sum()
        avg_daily_spend = df['spend'].mean()
        
        # Find optimal spend point (where marginal ROAS starts declining)
        optimal_spend = self._find_optimal_spend(df)
        
        # Calculate weekly aggregates for trend analysis
        df['week'] = pd.to_datetime(df['date']).dt.to_period('W')
        weekly_metrics = df.groupby('week').agg({
            'spend': 'sum',
            'revenue': 'sum',
            'conversions': 'sum'
        }).reset_index()
        
        # Find best performing periods
        df['roas'] = df['revenue'] / df['spend']
        best_days = df.nlargest(5, 'roas')[['date', 'roas', 'revenue']].to_dict('records')
        
        return {
            'channel': channel,
            'period': {'start': start_date, 'end': end_date},
            'metrics': {
                'total_spend': round(total_spend, 2),
                'total_revenue': round(total_revenue, 2),
                'roas': round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
                'avg_daily_spend': round(avg_daily_spend, 2),
                'optimal_daily_spend': optimal_spend,
                'current_daily_spend': round(df.tail(7)['spend'].mean(), 2),  # Last 7 days average
                'opportunity': self._calculate_opportunity(optimal_spend, avg_daily_spend)
            },
            'time_series': {
                'daily': df[['date', 'spend', 'revenue', 'conversions']].to_dict('records'),
                'weekly': weekly_metrics.to_dict('records')
            },
            'best_performing_days': best_days
        }
    
    def _find_optimal_spend(self, df: pd.DataFrame) -> float:
        """Find optimal spend point using marginal ROAS analysis"""
        # Sort by spend
        df_sorted = df.sort_values('spend')
        
        # Calculate rolling marginal ROAS
        window = 7
        df_sorted['marginal_revenue'] = df_sorted['revenue'].diff(window)
        df_sorted['marginal_spend'] = df_sorted['spend'].diff(window)
        df_sorted['marginal_roas'] = df_sorted['marginal_revenue'] / df_sorted['marginal_spend']
        
        # Find where marginal ROAS drops below overall ROAS
        overall_roas = df['revenue'].sum() / df['spend'].sum()
        
        # Find the spend level where marginal ROAS < overall ROAS * 0.8
        declining_point = df_sorted[df_sorted['marginal_roas'] < overall_roas * 0.8]
        
        if not declining_point.empty:
            return round(declining_point.iloc[0]['spend'], 2)
        else:
            # If no clear declining point, use 90th percentile of spend
            return round(df['spend'].quantile(0.9), 2)
    
    def _calculate_opportunity(self, optimal_spend: float, current_spend: float) -> str:
        """Calculate optimization opportunity"""
        difference = optimal_spend - current_spend
        
        if abs(difference) < 100:
            return "Spend is optimized"
        elif difference > 0:
            return f"Increase by ${abs(difference):.0f}/day"
        else:
            return f"Reduce by ${abs(difference):.0f}/day"
    
    def get_channel_trends(self, channel: str, days: int = 30) -> Dict:
        """Get recent trends for a channel"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        recent_data = self.db.query(
            func.date_trunc('week', DailyMarketingData.date).label('week'),
            func.sum(DailyMarketingData.spend).label('spend'),
            func.sum(DailyMarketingData.revenue).label('revenue'),
            func.sum(DailyMarketingData.conversions).label('conversions')
        ).filter(
            and_(
                DailyMarketingData.channel == channel,
                DailyMarketingData.date >= start_date
            )
        ).group_by('week').order_by('week').all()
        
        trends = []
        for row in recent_data:
            roas = float(row.revenue) / float(row.spend) if row.spend > 0 else 0
            trends.append({
                'week': row.week.strftime('%Y-%m-%d'),
                'spend': float(row.spend),
                'revenue': float(row.revenue),
                'conversions': int(row.conversions),
                'roas': round(roas, 2)
            })
        
        return {
            'channel': channel,
            'period_days': days,
            'trends': trends
        }