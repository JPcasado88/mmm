from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from ..models.models import DailyMarketingData, AttributionResult

class AttributionService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_attribution(self, start_date: str, end_date: str, model_type: str = 'linear') -> Dict:
        """Calculate attribution for a given period and model"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            # Handle date parsing errors
            return {'error': f'Invalid date format: {str(e)}'}
        
        # Get conversion data
        conversions_data = self._get_conversions_data(start, end)
        
        # Apply attribution model
        if model_type == 'last_click':
            attributed = self._last_click_attribution(conversions_data)
        elif model_type == 'linear':
            attributed = self._linear_attribution(conversions_data)
        elif model_type == 'time_decay':
            attributed = self._time_decay_attribution(conversions_data)
        elif model_type == 'u_shaped':
            attributed = self._u_shaped_attribution(conversions_data)
        elif model_type == 'data_driven':
            attributed = self._data_driven_attribution(conversions_data)
        else:
            return {'error': f'Unknown attribution model: {model_type}'}
        
        # Save results
        self._save_attribution_results(attributed, model_type, start, end)
        
        return {
            'model': model_type,
            'period': {'start': start_date, 'end': end_date},
            'results': attributed,
            'summary': self._calculate_attribution_summary(attributed)
        }
    
    def _get_conversions_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Get conversion data with touchpoints"""
        # For simplicity, we'll simulate touchpoint data based on channel interactions
        # In a real system, this would come from user journey tracking
        
        # Convert datetime to date for comparison
        start_date = start.date() if hasattr(start, 'date') else start
        end_date = end.date() if hasattr(end, 'date') else end
        
        data = self.db.query(DailyMarketingData).filter(
            and_(
                DailyMarketingData.date >= start_date,
                DailyMarketingData.date <= end_date
            )
        ).all()
        
        # Convert to DataFrame with aggregation by channel
        channel_data = {}
        for d in data:
            if d.channel not in channel_data:
                channel_data[d.channel] = {
                    'conversions': 0,
                    'revenue': 0.0,
                    'clicks': 0
                }
            channel_data[d.channel]['conversions'] += d.conversions
            channel_data[d.channel]['revenue'] += float(d.revenue)
            channel_data[d.channel]['clicks'] += d.clicks
        
        # Create DataFrame from aggregated data
        if channel_data:
            df_data = []
            for channel, metrics in channel_data.items():
                df_data.append({
                    'date': end_date,
                    'channel': channel,
                    'conversions': metrics['conversions'],
                    'revenue': metrics['revenue'],
                    'clicks': metrics['clicks']
                })
            df = pd.DataFrame(df_data)
        else:
            # Create empty DataFrame with proper structure
            df = pd.DataFrame(columns=['date', 'channel', 'conversions', 'revenue', 'clicks'])
        
        return df
    
    def _last_click_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Last click attribution - 100% credit to last touchpoint"""
        results = []
        
        # If DataFrame is empty, return default channels with zero values
        if df.empty:
            for channel in ['Google Ads', 'Meta Ads', 'Email', 'TikTok', 'Affiliate']:
                results.append({
                    'channel': channel,
                    'attributed_conversions': 0,
                    'attributed_revenue': 0.0,
                    'percentage': 0.0
                })
            return results
        
        for channel in df['channel'].unique():
            channel_data = df[df['channel'] == channel]
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(channel_data['conversions'].sum()),
                'attributed_revenue': float(channel_data['revenue'].sum()),
                'percentage': 0  # Will calculate after
            })
        
        # Calculate percentages
        total_conversions = sum(r['attributed_conversions'] for r in results)
        for r in results:
            r['percentage'] = round((r['attributed_conversions'] / total_conversions * 100), 2) if total_conversions > 0 else 0
        
        return results
    
    def _linear_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Linear attribution - Equal credit to all touchpoints"""
        results = []
        
        # If DataFrame is empty, return default channels with zero values
        if df.empty:
            for channel in ['Google Ads', 'Meta Ads', 'Email', 'TikTok', 'Affiliate']:
                results.append({
                    'channel': channel,
                    'attributed_conversions': 0,
                    'attributed_revenue': 0.0,
                    'percentage': 0.0
                })
            return results
        
        # Equal distribution across all channels
        total_conversions = df['conversions'].sum()
        total_revenue = df['revenue'].sum()
        num_channels = len(df['channel'].unique())
        
        if num_channels == 0:
            return results
        
        for channel in df['channel'].unique():
            results.append({
                'channel': channel,
                'attributed_conversions': int(total_conversions / num_channels),
                'attributed_revenue': float(total_revenue / num_channels),
                'percentage': round(100 / num_channels, 2)
            })
        
        return results
    
    def _time_decay_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Time decay attribution - More credit to recent touchpoints"""
        results = []
        
        # If DataFrame is empty, return default channels with zero values
        if df.empty:
            for channel in ['Google Ads', 'Meta Ads', 'Email', 'TikTok', 'Affiliate']:
                results.append({
                    'channel': channel,
                    'attributed_conversions': 0,
                    'attributed_revenue': 0.0,
                    'percentage': 0.0
                })
            return results
        
        # For aggregated data, use channel performance as weight
        total_conversions = df['conversions'].sum()
        total_revenue = df['revenue'].sum()
        
        # Weight by recent performance (using conversions as proxy)
        for _, row in df.iterrows():
            channel = row['channel']
            # Channels with more conversions get more credit (simulating recency)
            weight = row['conversions'] / total_conversions if total_conversions > 0 else 0
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(row['conversions']),
                'attributed_revenue': float(row['revenue']),
                'percentage': round(weight * 100, 2)
            })
        
        return results
    
    def _u_shaped_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """U-shaped attribution - 40% first, 40% last, 20% middle touchpoints"""
        # Simulate based on channel characteristics
        first_touch_weight = {
            'Google Ads': 0.35,  # Often first discovery
            'Meta Ads': 0.30,
            'TikTok': 0.25,
            'Email': 0.05,      # Rarely first touch
            'Affiliate': 0.05
        }
        
        last_touch_weight = {
            'Google Ads': 0.30,
            'Meta Ads': 0.20,
            'Email': 0.25,      # Often closes deals
            'Affiliate': 0.20,
            'TikTok': 0.05
        }
        
        results = []
        total_conversions = df['conversions'].sum()
        total_revenue = df['revenue'].sum()
        
        for channel in df['channel'].unique():
            # U-shaped weight = 40% first + 40% last + 20% middle
            first_weight = first_touch_weight.get(channel, 0.2) * 0.4
            last_weight = last_touch_weight.get(channel, 0.2) * 0.4
            middle_weight = 0.2 / len(df['channel'].unique())  # Equal split for middle
            
            total_weight = first_weight + last_weight + middle_weight
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(total_conversions * total_weight),
                'attributed_revenue': float(total_revenue * total_weight),
                'percentage': round(total_weight * 100, 2)
            })
        
        return results
    
    def _data_driven_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Data-driven attribution using simplified Shapley values"""
        # Calculate channel contribution using conversion rates and interactions
        results = []
        
        # Calculate channel efficiency metrics
        channel_metrics = {}
        for channel in df['channel'].unique():
            channel_data = df[df['channel'] == channel]
            
            # Calculate conversion rate when channel is present
            conversion_rate = channel_data['conversions'].sum() / channel_data['clicks'].sum() if channel_data['clicks'].sum() > 0 else 0
            
            # Calculate average revenue per conversion
            avg_revenue = channel_data['revenue'].sum() / channel_data['conversions'].sum() if channel_data['conversions'].sum() > 0 else 0
            
            channel_metrics[channel] = {
                'conversion_rate': conversion_rate,
                'avg_revenue': avg_revenue,
                'total_conversions': channel_data['conversions'].sum(),
                'total_revenue': channel_data['revenue'].sum()
            }
        
        # Calculate Shapley-like values based on incremental contribution
        total_conversions = df['conversions'].sum()
        total_revenue = df['revenue'].sum()
        
        # Baseline (no channels) = 0
        # Each channel's contribution = its incremental value
        for channel in df['channel'].unique():
            metrics = channel_metrics[channel]
            
            # Incremental contribution based on conversion rate and volume
            contribution_score = metrics['conversion_rate'] * metrics['total_conversions']
            
            # Normalize across all channels
            total_score = sum(channel_metrics[ch]['conversion_rate'] * channel_metrics[ch]['total_conversions'] 
                            for ch in channel_metrics)
            
            if total_score > 0:
                attribution_weight = contribution_score / total_score
            else:
                attribution_weight = 1 / len(df['channel'].unique())
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(total_conversions * attribution_weight),
                'attributed_revenue': float(total_revenue * attribution_weight),
                'percentage': round(attribution_weight * 100, 2)
            })
        
        return results
    
    def _save_attribution_results(self, results: List[Dict], model_type: str, start: datetime, end: datetime):
        """Save attribution results to database"""
        # Clear existing results for this period and model
        self.db.query(AttributionResult).filter(
            and_(
                AttributionResult.model_type == model_type,
                AttributionResult.date >= start,
                AttributionResult.date <= end
            )
        ).delete()
        
        # Save new results
        for result in results:
            attribution = AttributionResult(
                date=end,  # Use end date for the attribution period
                channel=result['channel'],
                model_type=model_type,
                attributed_conversions=result['attributed_conversions'],
                attributed_revenue=result['attributed_revenue']
            )
            self.db.add(attribution)
        
        self.db.commit()
    
    def _calculate_attribution_summary(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics for attribution results"""
        total_conversions = sum(r['attributed_conversions'] for r in results)
        total_revenue = sum(r['attributed_revenue'] for r in results)
        
        # Find top and bottom performers
        sorted_results = sorted(results, key=lambda x: x['attributed_revenue'], reverse=True)
        
        return {
            'total_attributed_conversions': total_conversions,
            'total_attributed_revenue': round(total_revenue, 2),
            'top_performer': {
                'channel': sorted_results[0]['channel'],
                'revenue': round(sorted_results[0]['attributed_revenue'], 2),
                'percentage': sorted_results[0]['percentage']
            },
            'bottom_performer': {
                'channel': sorted_results[-1]['channel'],
                'revenue': round(sorted_results[-1]['attributed_revenue'], 2),
                'percentage': sorted_results[-1]['percentage']
            }
        }
    
    def compare_attribution_models(self, start_date: str, end_date: str) -> Dict:
        """Compare results across different attribution models"""
        models = ['last_click', 'linear', 'time_decay', 'u_shaped', 'data_driven']
        comparison = {}
        
        try:
            for model in models:
                result = self.calculate_attribution(start_date, end_date, model)
                comparison[model] = result.get('results', [])
        except Exception as e:
            print(f"Error in attribution comparison: {str(e)}")
            # Return empty results on error
            for model in models:
                comparison[model] = []
        
        # Calculate variance across models
        channel_variance = {}
        channels = list(set(r['channel'] for results in comparison.values() for r in results))
        
        for channel in channels:
            percentages = [
                next((r['percentage'] for r in results if r['channel'] == channel), 0)
                for results in comparison.values()
            ]
            channel_variance[channel] = {
                'min': min(percentages),
                'max': max(percentages),
                'variance': round(np.var(percentages), 2),
                'mean': round(np.mean(percentages), 2)
            }
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'models': comparison,
            'channel_variance': channel_variance,
            'recommendation': self._recommend_attribution_model(channel_variance)
        }
    
    def _recommend_attribution_model(self, variance_data: Dict) -> str:
        """Recommend the most appropriate attribution model based on data patterns"""
        # Simple recommendation logic
        avg_variance = np.mean([ch['variance'] for ch in variance_data.values()])
        
        if avg_variance < 5:
            return "Models show similar results. Linear attribution is recommended for simplicity."
        elif avg_variance < 15:
            return "Moderate variance between models. U-shaped attribution recommended to balance first and last touch."
        else:
            return "High variance between models. Data-driven attribution recommended for accuracy."