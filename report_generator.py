from typing import Dict
from datetime import datetime
from config import IVAN_CONTACT

class ReportGenerator:
    def __init__(self):
        self.ivan_contact = IVAN_CONTACT
    
    def create_analysis_report(self, analysis: Dict, cost_info: Dict, 
                              timeline: Dict, client_info: Dict) -> str:
        """Создает детальный отчет анализа для Ивана"""
        
        report = f"""🏠 **АНАЛИЗ ЗАЯВКИ КЛИЕНТА**
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

👤 **ИНФОРМАЦИЯ О КЛИЕНТЕ:**
• Имя: {client_info.get('name', 'Не указано')}
• Телефон: {client_info.get('phone', 'Не указан')}
• Адрес: {client_info.get('address', 'Не указан')}
• Количество сообщений: {client_info.get('message_count', 0)}

📊 **АНАЛИЗ ПОЛА:**
• Тип покрытия: {self._get_floor_type_description(analysis.get('floor_type', 'unknown'))}
• Состояние: {self._get_condition_description(analysis.get('condition', 'unknown'))}
• Площадь: ~{analysis.get('total_area_estimate', 0)} кв.м
• Сложность работ: {self._get_complexity_description(analysis.get('work_complexity', 'medium'))}
• Проанализировано изображений: {analysis.get('images_analyzed', 0)}

⚠️ **ПОВРЕЖДЕНИЯ:**
{self._format_damages(analysis.get('damages', []))}

🔧 **РЕКОМЕНДУЕМЫЕ РАБОТЫ:**
{self._format_recommendations(analysis.get('recommendations', []))}

💰 **СТОИМОСТЬ:**
• Базовая цена: {cost_info['base_price_per_sqm']}₪/кв.м
• Базовая стоимость: {cost_info['base_cost']}₪
• Коэффициенты:
  - Состояние: x{cost_info['condition_multiplier']}
  - Сложность: x{cost_info['complexity_multiplier']}
  - Повреждения: x{cost_info['damage_multiplier']}
• **ИТОГО: {cost_info['min_cost']}-{cost_info['max_cost']}₪**
• **РЕКОМЕНДУЕМАЯ ЦЕНА: {cost_info['recommended_cost']}₪**

⏱️ **СРОКИ ВЫПОЛНЕНИЯ:**
• Тип работ: {timeline['work_type']}
• Время: {timeline['min_days']}-{timeline['max_days']} дней
• Рекомендуемый срок: {timeline['estimated_days']} дней

📝 **ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:**
{self._format_additional_info(analysis, client_info)}

---
🤖 *Анализ выполнен ИИ-ботом {self.ivan_contact['name']}а*
📞 *Контакт: {self.ivan_contact['phone']}*
"""
        return report
    
    def create_client_response_template(self, analysis: Dict, cost_info: Dict, 
                                      timeline: Dict, client_info: Dict) -> str:
        """Создает шаблон ответа для клиента"""
        
        client_name = client_info.get('name', 'Клиент')
        
        template = f"""Привет {client_name}! 👋

Проанализировал твои фотографии. Вот что вижу:

🏠 **Тип покрытия:** {self._get_floor_type_description(analysis.get('floor_type', 'unknown'))}
📐 **Площадь:** примерно {analysis.get('total_area_estimate', 0)} кв.м
⚠️ **Состояние:** {self._get_condition_description(analysis.get('condition', 'unknown'))}

{self._format_damages_for_client(analysis.get('damages', []))}

🔧 **Что нужно сделать:**
{self._format_recommendations_for_client(analysis.get('recommendations', []))}

💰 **Стоимость работ:** {cost_info['recommended_cost']}₪
⏱️ **Время выполнения:** {timeline['estimated_days']} дней

Когда удобно приехать для точного замера?

С уважением,
{self.ivan_contact['name']} 🔨
📞 {self.ivan_contact['phone']}
"""
        return template
    
    def create_quick_summary(self, analysis: Dict, cost_info: Dict) -> str:
        """Создает краткую сводку для быстрого просмотра"""
        
        floor_type = self._get_floor_type_description(analysis.get('floor_type', 'unknown'))
        condition = analysis.get('condition', 'unknown')
        area = analysis.get('total_area_estimate', 0)
        price = cost_info['recommended_cost']
        
        summary = f"""📋 **КРАТКАЯ СВОДКА**

🏠 {floor_type} | 📐 {area} кв.м | ⚠️ {condition}
💰 {price}₪ | 🔧 {len(analysis.get('recommendations', []))} рекомендаций
📸 Проанализировано: {analysis.get('images_analyzed', 0)} изображений
"""
        return summary
    
    def _get_floor_type_description(self, floor_type: str) -> str:
        """Возвращает описание типа пола"""
        descriptions = {
            'parquet': 'Паркет',
            'laminate': 'Ламинат',
            'tiles': 'Плитка',
            'linoleum': 'Линолеум',
            'carpet': 'Ковролин',
            'concrete': 'Бетон',
            'unknown': 'Неопределенный тип'
        }
        return descriptions.get(floor_type, 'Неопределенный тип')
    
    def _get_condition_description(self, condition: str) -> str:
        """Возвращает описание состояния"""
        descriptions = {
            'excellent': 'Отличное',
            'good': 'Хорошее',
            'fair': 'Удовлетворительное',
            'poor': 'Плохое',
            'unknown': 'Требует осмотра'
        }
        return descriptions.get(condition, 'Требует осмотра')
    
    def _get_complexity_description(self, complexity: str) -> str:
        """Возвращает описание сложности работ"""
        descriptions = {
            'low': 'Низкая (простой ремонт)',
            'medium': 'Средняя (стандартные работы)',
            'high': 'Высокая (сложный ремонт)'
        }
        return descriptions.get(complexity, 'Средняя')
    
    def _format_damages(self, damages: list) -> str:
        """Форматирует список повреждений"""
        if not damages:
            return "• Серьезных повреждений не обнаружено"
        
        formatted = []
        for damage in damages:
            severity_emoji = {
                'minor': '🟡',
                'moderate': '🟠', 
                'severe': '🔴'
            }
            emoji = severity_emoji.get(damage.get('severity', 'minor'), '🟡')
            formatted.append(f"• {emoji} {damage.get('description', 'Повреждение')}")
        
        return '\n'.join(formatted)
    
    def _format_damages_for_client(self, damages: list) -> str:
        """Форматирует повреждения для клиента"""
        if not damages:
            return ""
        
        severe_damages = [d for d in damages if d.get('severity') == 'severe']
        if severe_damages:
            return f"\n⚠️ **Обнаружены серьезные повреждения:** {len(severe_damages)} шт.\n"
        
        return f"\n⚠️ **Обнаружены повреждения:** {len(damages)} шт.\n"
    
    def _format_recommendations(self, recommendations: list) -> str:
        """Форматирует рекомендации"""
        if not recommendations:
            return "• Дополнительный осмотр на месте"
        
        formatted = []
        for i, rec in enumerate(recommendations, 1):
            formatted.append(f"{i}. {rec}")
        
        return '\n'.join(formatted)
    
    def _format_recommendations_for_client(self, recommendations: list) -> str:
        """Форматирует рекомендации для клиента"""
        if not recommendations:
            return "Требуется осмотр на месте для точной оценки"
        
        # Берем первые 3 самые важные рекомендации
        main_recs = recommendations[:3]
        formatted = []
        for rec in main_recs:
            formatted.append(f"• {rec}")
        
        return '\n'.join(formatted)
    
    def _format_additional_info(self, analysis: Dict, client_info: Dict) -> str:
        """Форматирует дополнительную информацию"""
        info_parts = []
        
        # Описания проблем от клиента
        if client_info.get('problem_descriptions'):
            info_parts.append("**Описание проблем от клиента:**")
            for desc in client_info['problem_descriptions'][:3]:  # Первые 3
                info_parts.append(f"• {desc}")
        
        # Контекст разговора
        if analysis.get('context'):
            context_lines = analysis['context'].split('\n')[-5:]  # Последние 5 строк
            if context_lines:
                info_parts.append("\n**Последние сообщения:**")
                for line in context_lines:
                    if line.strip():
                        info_parts.append(f"• {line.strip()}")
        
        return '\n'.join(info_parts) if info_parts else "Дополнительная информация отсутствует"

