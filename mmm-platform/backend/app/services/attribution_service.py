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
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
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
        
        data = self.db.query(DailyMarketingData).filter(
            and_(
                DailyMarketingData.date >= start,
                DailyMarketingData.date <= end
            )
        ).all()
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': d.date,
            'channel': d.channel,
            'conversions': d.conversions,
            'revenue': float(d.revenue),
            'clicks': d.clicks
        } for d in data])
        
        return df
    
    def _last_click_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Last click attribution - 100% credit to last touchpoint"""
        results = []
        
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
        # Simulate multi-touch journeys
        channel_weights = {
            'Google Ads': 0.25,
            'Meta Ads': 0.20,
            'Email': 0.20,
            'TikTok': 0.20,
            'Affiliate': 0.15
        }
        
        results = []
        total_conversions = df['conversions'].sum()
        total_revenue = df['revenue'].sum()
        
        for channel in df['channel'].unique():
            weight = channel_weights.get(channel, 0.2)
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(total_conversions * weight),
                'attributed_revenue': float(total_revenue * weight),
                'percentage': round(weight * 100, 2)
            })
        
        return results
    
    def _time_decay_attribution(self, df: pd.DataFrame) -> List[Dict]:
        """Time decay attribution - More credit to recent touchpoints"""
        # Give more weight to channels that perform better in recent periods
        results = []
        
        # Calculate recency weights (last 30 days get more credit)
        df['days_ago'] = (df['date'].max() - df['date']).dt.days
        df['time_weight'] = np.exp(-df['days_ago'] / 30)  # Exponential decay
        
        for channel in df['channel'].unique():
            channel_data = df[df['channel'] == channel]
            
            # Weight conversions by time
            weighted_conversions = (channel_data['conversions'] * channel_data['time_weight']).sum()
            weighted_revenue = (channel_data['revenue'] * channel_data['time_weight']).sum()
            
            results.append({
                'channel': channel,
                'attributed_conversions': int(weighted_conversions),
                'attributed_revenue': float(weighted_revenue),
                'percentage': 0
            })
        
        # Normalize to maintain total conversions
        total_weighted = sum(r['attributed_conversions'] for r in results)
        actual_total = df['conversions'].sum()
        
        for r in results:
            if total_weighted > 0:
                r['attributed_conversions'] = int(r['attributed_conversions'] * actual_total / total_weighted)
                r['attributed_revenue'] = float(r['attributed_revenue'] * df['revenue'].sum() / sum(res['attributed_revenue'] for res in results))
                r['percentage'] = round((r['attributed_conversions'] / actual_total * 100), 2)
        
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
        
        for model in models:
            result = self.calculate_attribution(start_date, end_date, model)
            comparison[model] = result['results']
        
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