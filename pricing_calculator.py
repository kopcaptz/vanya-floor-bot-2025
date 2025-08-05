from typing import Dict
from config import BASE_PRICES, CONDITION_MULTIPLIERS

class PricingCalculator:
    def __init__(self):
        self.base_prices = BASE_PRICES
        self.condition_multipliers = CONDITION_MULTIPLIERS
    
    def calculate_project_cost(self, analysis: Dict) -> Dict:
        """
        Рассчитывает стоимость проекта на основе анализа
        
        Args:
            analysis: Результат анализа изображений
            
        Returns:
            Dict с расчетом стоимости
        """
        floor_type = analysis.get('floor_type', 'unknown')
        condition = analysis.get('condition', 'unknown')
        area = analysis.get('total_area_estimate', 20)
        work_complexity = analysis.get('work_complexity', 'medium')
        damages = analysis.get('damages', [])
        
        # Базовая цена за кв.м
        base_price = self.base_prices.get(floor_type, self.base_prices['unknown'])
        
        # Коэффициент состояния
        condition_multiplier = self.condition_multipliers.get(condition, 1.3)
        
        # Коэффициент сложности работ
        complexity_multipliers = {
            'low': 1.0,
            'medium': 1.3,
            'high': 1.8
        }
        complexity_multiplier = complexity_multipliers.get(work_complexity, 1.3)
        
        # Коэффициент повреждений
        damage_multiplier = self._calculate_damage_multiplier(damages)
        
        # Расчет базовой стоимости
        base_cost = base_price * area
        
        # Применяем все коэффициенты
        total_multiplier = condition_multiplier * complexity_multiplier * damage_multiplier
        final_cost = base_cost * total_multiplier
        
        # Создаем диапазон цен (±15%)
        min_cost = int(final_cost * 0.85)
        max_cost = int(final_cost * 1.15)
        recommended_cost = int(final_cost)
        
        return {
            'base_price_per_sqm': base_price,
            'area': area,
            'base_cost': int(base_cost),
            'condition_multiplier': condition_multiplier,
            'complexity_multiplier': complexity_multiplier,
            'damage_multiplier': damage_multiplier,
            'total_multiplier': round(total_multiplier, 2),
            'min_cost': min_cost,
            'max_cost': max_cost,
            'recommended_cost': recommended_cost,
            'currency': 'ILS',
            'breakdown': self._create_cost_breakdown(
                base_cost, condition_multiplier, complexity_multiplier, damage_multiplier
            )
        }
    
    def _calculate_damage_multiplier(self, damages: list) -> float:
        """Рассчитывает коэффициент на основе повреждений"""
        if not damages:
            return 1.0
        
        multiplier = 1.0
        
        for damage in damages:
            severity = damage.get('severity', 'minor')
            if severity == 'minor':
                multiplier += 0.1
            elif severity == 'moderate':
                multiplier += 0.2
            elif severity == 'severe':
                multiplier += 0.4
        
        # Максимальный коэффициент повреждений - 2.0
        return min(multiplier, 2.0)
    
    def _create_cost_breakdown(self, base_cost: float, condition_mult: float, 
                              complexity_mult: float, damage_mult: float) -> Dict:
        """Создает детальную разбивку стоимости"""
        return {
            'base_work': int(base_cost),
            'condition_adjustment': int(base_cost * (condition_mult - 1)),
            'complexity_adjustment': int(base_cost * condition_mult * (complexity_mult - 1)),
            'damage_adjustment': int(base_cost * condition_mult * complexity_mult * (damage_mult - 1))
        }
    
    def get_work_timeline(self, analysis: Dict, cost_info: Dict) -> Dict:
        """Рассчитывает временные рамки выполнения работ"""
        area = analysis.get('total_area_estimate', 20)
        work_complexity = analysis.get('work_complexity', 'medium')
        floor_type = analysis.get('floor_type', 'unknown')
        
        # Базовое время работы (дни на 10 кв.м)
        base_days_per_10sqm = {
            'parquet': 2,
            'laminate': 1,
            'tiles': 3,
            'linoleum': 1,
            'unknown': 2
        }
        
        base_days = base_days_per_10sqm.get(floor_type, 2)
        
        # Рассчитываем время для данной площади
        estimated_days = (area / 10) * base_days
        
        # Коэффициенты сложности
        complexity_time_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }
        
        time_multiplier = complexity_time_multipliers.get(work_complexity, 1.5)
        final_days = estimated_days * time_multiplier
        
        # Минимум 1 день, максимум 14 дней
        final_days = max(1, min(14, final_days))
        
        return {
            'estimated_days': int(final_days),
            'min_days': max(1, int(final_days * 0.8)),
            'max_days': int(final_days * 1.3),
            'work_type': self._get_work_description(floor_type, work_complexity)
        }
    
    def _get_work_description(self, floor_type: str, complexity: str) -> str:
        """Возвращает описание типа работ"""
        work_descriptions = {
            'parquet': {
                'low': 'Легкий ремонт паркета',
                'medium': 'Реставрация паркета',
                'high': 'Полная замена паркета'
            },
            'laminate': {
                'low': 'Замена отдельных планок ламината',
                'medium': 'Частичная замена ламината',
                'high': 'Полная замена ламината'
            },
            'tiles': {
                'low': 'Замена отдельных плиток',
                'medium': 'Частичная замена плитки',
                'high': 'Полная замена плитки'
            },
            'linoleum': {
                'low': 'Ремонт линолеума',
                'medium': 'Частичная замена линолеума',
                'high': 'Полная замена линолеума'
            }
        }
        
        return work_descriptions.get(floor_type, {}).get(complexity, 'Ремонт напольного покрытия')

