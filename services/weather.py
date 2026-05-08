# @TASK T-REFACTOR - Weather alert logic extracted from app.py
# @SPEC docs/planning/02-trd.md#weather-alerts
import logging
import requests
from datetime import datetime

from config import KMA_API_KEY

logger = logging.getLogger(__name__)
WEATHER_ALERT_CACHE = {'data': None, 'ts': 0}
WEATHER_ALERT_CACHE_TTL = 300  # 5분


def get_alert_level(title):
    """특보 제목에서 경보 수준 추출"""
    if '경보' in title:
        return 'warning'
    elif '주의보' in title:
        return 'watch'
    elif '예비' in title:
        return 'advisory'
    return 'info'


def fetch_weather_alerts(kma_api_key, session):
    """기상청 특보 API를 호출하여 울산 지역 특보 목록을 반환한다.

    Args:
        kma_api_key: data.go.kr 기상청 특보 서비스 키.
        session: ``requests.Session`` (또는 호환 객체) HTTP 호출용.

    Returns:
        dict — success, alerts, has_alerts 키를 포함하며,
        상황에 따라 updated_at, message, error 키가 추가된다.
    """
    if not kma_api_key:
        return {
            'success': True,
            'alerts': [],
            'has_alerts': False,
            'message': '기상청 API 키가 설정되지 않았습니다.'
        }

    try:
        base_url = "https://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnList"
        params = {
            'serviceKey': kma_api_key,
            'pageNo': 1,
            'numOfRows': 10,
            'dataType': 'JSON',
            'stnId': '159'  # 울산 지점 코드
        }

        response = session.get(base_url, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning(f"기상청 API 응답 오류: {response.status_code}")
            return {
                'success': False,
                'alerts': [],
                'has_alerts': False,
                'error': '기상 정보를 가져올 수 없습니다.'
            }

        data = response.json()

        alerts = []
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

        if isinstance(items, dict):
            items = [items]

        for item in items:
            title = item.get('t1', '') or item.get('title', '')
            content = item.get('t2', '') or item.get('other', '')
            tm_fc = item.get('tmFc', '')
            tm_seq = item.get('tmSeq', '')

            if '울산' in title or '울산' in content or '전국' in title:
                alerts.append({
                    'title': title,
                    'content': content[:200] if content else '',
                    'issued_at': tm_fc,
                    'seq': tm_seq,
                    'level': get_alert_level(title)
                })

        return {
            'success': True,
            'alerts': alerts,
            'has_alerts': len(alerts) > 0,
            'updated_at': datetime.now().isoformat()
        }

    except requests.exceptions.Timeout:
        logger.error("기상청 API 타임아웃")
        return {
            'success': False,
            'alerts': [],
            'has_alerts': False,
            'error': '기상 정보 요청 시간 초과'
        }
    except Exception as e:
        logger.error(f"기상청 API 오류: {e}")
        return {
            'success': False,
            'alerts': [],
            'has_alerts': False,
            'error': '기상 정보 조회 중 오류 발생'
        }
