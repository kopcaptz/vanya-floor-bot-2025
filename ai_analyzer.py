import openai
import base64
import json
import logging
from typing import Dict, List, Optional
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

class FloorAnalyzer:
    def __init__(self, api_key: str = OPENAI_API_KEY):
        if not api_key:
            # Используем переменную окружения если ключ не передан
            import os
            api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            # Создаем заглушку если нет ключа
            self.client = None
            logger.warning("OpenAI API key not provided, image analysis will be disabled")
    
    def analyze_floor_image(self, image_path: str, context: str = "") -> Dict:
        """
        Анализирует изображение пола с учетом контекста разговора
        
        Args:
            image_path: Путь к изображению
            context: Контекст разговора с клиентом
            
        Returns:
            Dict с результатами анализа
        """
        if not self.client:
            return {
                'success': False,
                'error': 'OpenAI API key not configured',
                'floor_type': 'unknown',
                'condition': 'unknown',
                'damages': [],
                'area_estimate': 20,
                'recommendations': ['Требуется настройка OpenAI API'],
                'cost_estimate': 0
            }
        
        try:
            # Конвертируем изображение в base64
            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Создаем промпт с контекстом
            prompt = self._create_analysis_prompt(context)
            
            # Отправляем запрос к OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                max_tokens=1500,
                temperature=0.1
            )
            
            # Парсим ответ
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Error analyzing floor image: {e}")
            return {
                'success': False,
                'error': str(e),
                'floor_type': 'unknown',
                'condition': 'unknown',
                'damages': [],
                'area_estimate': 0,
                'recommendations': [],
                'cost_estimate': 0
            }
    
    def _create_analysis_prompt(self, context: str) -> str:
        """Создает промпт для анализа изображения"""
        prompt = f"""
Ты эксперт по напольным покрытиям в Израиле с 15-летним опытом работы.

КОНТЕКСТ РАЗГОВОРА С КЛИЕНТОМ:
{context if context else "Контекст отсутствует"}

Проанализируй изображение пола и предоставь детальную оценку в формате JSON:

{{
    "floor_type": "тип покрытия (parquet/laminate/tiles/linoleum/carpet/concrete)",
    "floor_type_hebrew": "название на иврите",
    "condition": "состояние (excellent/good/fair/poor)",
    "condition_description": "подробное описание состояния",
    "damages": [
        {{
            "type": "тип повреждения",
            "severity": "серьезность (minor/moderate/severe)",
            "description": "описание повреждения"
        }}
    ],
    "area_estimate": "примерная площадь в кв.м (число)",
    "room_type": "тип помещения (living_room/bedroom/kitchen/bathroom/hallway/balcony)",
    "recommendations": [
        "рекомендация 1",
        "рекомендация 2"
    ],
    "work_complexity": "сложность работ (low/medium/high)",
    "urgency": "срочность (low/medium/high)",
    "estimated_duration": "время выполнения в днях",
    "special_notes": "особые замечания",
    "confidence_level": "уверенность в анализе (0-100)"
}}

ВАЖНЫЕ ОСОБЕННОСТИ ИЗРАИЛЬСКОГО РЫНКА:
- Учитывай климатические условия (жаркое лето, влажность)
- Стандартные размеры помещений в израильских квартирах
- Популярные материалы: керамическая плитка, ламинат, паркет
- Типичные проблемы: трещины от жары, износ от песка

Будь максимально точным и практичным в рекомендациях.
"""
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Парсит ответ от OpenAI"""
        try:
            # Пытаемся распарсить JSON
            analysis = json.loads(response_text)
            analysis['success'] = True
            return analysis
        except json.JSONDecodeError:
            # Если JSON не валидный, пытаемся извлечь информацию текстом
            logger.warning("Failed to parse JSON response, extracting manually")
            return self._extract_analysis_from_text(response_text)
    
    def _extract_analysis_from_text(self, text: str) -> Dict:
        """Извлекает информацию из текстового ответа"""
        # Базовый парсер для случаев, когда JSON не валидный
        analysis = {
            'success': True,
            'floor_type': 'unknown',
            'condition': 'unknown',
            'damages': [],
            'area_estimate': 20,  # Дефолтное значение
            'recommendations': [],
            'work_complexity': 'medium',
            'urgency': 'medium',
            'estimated_duration': '1-2',
            'raw_response': text
        }
        
        # Простое извлечение ключевых слов
        text_lower = text.lower()
        
        # Определяем тип пола
        if any(word in text_lower for word in ['паркет', 'parquet']):
            analysis['floor_type'] = 'parquet'
        elif any(word in text_lower for word in ['ламинат', 'laminate']):
            analysis['floor_type'] = 'laminate'
        elif any(word in text_lower for word in ['плитка', 'tiles', 'керамика']):
            analysis['floor_type'] = 'tiles'
        elif any(word in text_lower for word in ['линолеум', 'linoleum']):
            analysis['floor_type'] = 'linoleum'
        
        # Определяем состояние
        if any(word in text_lower for word in ['отличное', 'excellent', 'хорошее']):
            analysis['condition'] = 'good'
        elif any(word in text_lower for word in ['плохое', 'poor', 'ужасное']):
            analysis['condition'] = 'poor'
        else:
            analysis['condition'] = 'fair'
        
        return analysis
    
    def analyze_multiple_images(self, image_files: List[Dict], context: str = "") -> Dict:
        """
        Анализирует несколько изображений и объединяет результаты
        
        Args:
            image_files: Список файлов изображений
            context: Контекст разговора
            
        Returns:
            Объединенный анализ всех изображений
        """
        individual_analyses = []
        
        for i, image_file in enumerate(image_files):
            if image_file['type'] == 'image':
                logger.info(f"Analyzing image {i+1}/{len(image_files)}: {image_file['name']}")
                analysis = self.analyze_floor_image(image_file['path'], context)
                analysis['image_name'] = image_file['name']
                individual_analyses.append(analysis)
        
        # Объединяем результаты
        return self._combine_analyses(individual_analyses, context)
    
    def _combine_analyses(self, analyses: List[Dict], context: str) -> Dict:
        """Объединяет результаты анализа нескольких изображений"""
        if not analyses:
            return {
                'success': False,
                'error': 'No images to analyze'
            }
        
        # Определяем наиболее частый тип пола
        floor_types = [a.get('floor_type', 'unknown') for a in analyses if a.get('success')]
        most_common_floor_type = max(set(floor_types), key=floor_types.count) if floor_types else 'unknown'
        
        # Определяем общее состояние (худшее из всех)
        conditions = [a.get('condition', 'unknown') for a in analyses if a.get('success')]
        condition_priority = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1, 'unknown': 0}
        worst_condition = min(conditions, key=lambda x: condition_priority.get(x, 0)) if conditions else 'unknown'
        
        # Собираем все повреждения
        all_damages = []
        for analysis in analyses:
            if analysis.get('success') and analysis.get('damages'):
                all_damages.extend(analysis['damages'])
        
        # Суммируем площадь (берем максимальную оценку)
        areas = [a.get('area_estimate', 0) for a in analyses if a.get('success')]
        total_area = max(areas) if areas else 20
        
        # Собираем все рекомендации
        all_recommendations = []
        for analysis in analyses:
            if analysis.get('success') and analysis.get('recommendations'):
                all_recommendations.extend(analysis['recommendations'])
        
        # Убираем дубликаты рекомендаций
        unique_recommendations = list(set(all_recommendations))
        
        # Определяем общую сложность работ
        complexities = [a.get('work_complexity', 'medium') for a in analyses if a.get('success')]
        complexity_priority = {'low': 1, 'medium': 2, 'high': 3}
        max_complexity = max(complexities, key=lambda x: complexity_priority.get(x, 2)) if complexities else 'medium'
        
        return {
            'success': True,
            'floor_type': most_common_floor_type,
            'condition': worst_condition,
            'total_area_estimate': total_area,
            'damages': all_damages,
            'recommendations': unique_recommendations,
            'work_complexity': max_complexity,
            'images_analyzed': len(analyses),
            'individual_analyses': analyses,
            'context': context
        }

