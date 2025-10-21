import asyncio
import aiohttp
import time
import statistics
from datetime import datetime, timedelta
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import pandas as pd

class ProfessionalLoadTester:
    def __init__(self, target_url, max_workers=50_000_000, test_duration=300_000):
        self.target_url = target_url
        self.max_workers = max_workers
        self.test_duration = test_duration
        self.results = []
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': []
        }
    
    async def make_request(self, session, request_id):
        """Создание одного HTTP запроса"""
        start_time = time.time()
        
        try:
            async with session.get(
                self.target_url, 
                timeout=aiohttp.ClientTimeout(total=10),
                headers={'User-Agent': f'LoadTest-Bot/{request_id}'}
            ) as response:
                
                response_time = time.time() - start_time
                
                result = {
                    'id': request_id,
                    'status': response.status,
                    'response_time': response_time,
                    'success': 200 <= response.status < 400,
                    'timestamp': datetime.now().isoformat()
                }
                
                if result['success']:
                    self.metrics['successful_requests'] += 1
                else:
                    self.metrics['failed_requests'] += 1
                
                self.metrics['response_times'].append(response_time)
                self.metrics['total_requests'] += 1
                
                return result
                
        except Exception as e:
            result = {
                'id': request_id,
                'status': 'error',
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.metrics['failed_requests'] += 1
            self.metrics['total_requests'] += 1
            return result
    
    async def worker(self, session, worker_id, requests_per_worker):
        """Рабочий процесс для генерации нагрузки"""
        for i in range(requests_per_worker):
            if time.time() > self.metrics['start_time'] + self.test_duration:
                break
                
            request_id = f"worker_{worker_id}_req_{i}"
            result = await self.make_request(session, request_id)
            self.results.append(result)
            
            # Контролируемая задержка между запросами
            await asyncio.sleep(0.1)
    
    async def run_load_test(self, target_rps=50):
        """Запуск основного теста нагрузки"""
        print(f"🚀 Запуск нагрузочного теста для {self.target_url}")
        print(f"⏱️ Длительность: {self.test_duration} сек")
        print(f"🎯 Целевой RPS: {target_rps}")
        print("-" * 50)
        
        self.metrics['start_time'] = time.time()
        
        # Конфигурация клиента
        connector = aiohttp.TCPConnector(limit=self.max_workers, limit_per_host=self.max_workers)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Расчет количества рабочих и запросов
            requests_per_worker = (target_rps * self.test_duration) // self.max_workers
            
            # Создание рабочих задач
            tasks = []
            for worker_id in range(self.max_workers):
                task = self.worker(session, worker_id, requests_per_worker)
                tasks.append(task)
            
            # Мониторинг прогресса
            monitoring_task = asyncio.create_task(self.monitor_progress())
            
            # Запуск всех задач
            await asyncio.gather(*tasks)
            
            # Остановка мониторинга
            monitoring_task.cancel()
        
        self.metrics['end_time'] = time.time()
        
        return self.generate_report()
    
    async def monitor_progress(self):
        """Мониторинг прогресса тестирования"""
        start_time = self.metrics['start_time']
        
        while time.time() < start_time + self.test_duration:
            elapsed = time.time() - start_time
            remaining = self.test_duration - elapsed
            
            current_rps = len([r for r in self.results 
                             if time.time() - r.get('timestamp', start_time) < 1])
            
            success_rate = (self.metrics['successful_requests'] / self.metrics['total_requests'] * 100 
                          if self.metrics['total_requests'] > 0 else 0)
            
            print(f"⏳ Прогресс: {elapsed:.1f}/{self.test_duration}сек | "
                  f"RPS: {current_rps} | Успешно: {success_rate:.1f}% | "
                  f"Запросов: {self.metrics['total_requests']}")
            
            await asyncio.sleep(1)
    
    def generate_report(self):
        """Генерация детального отчета"""
        total_time = self.metrics['end_time'] - self.metrics['start_time']
        actual_rps = self.metrics['total_requests'] / total_time
        
        response_times = self.metrics['response_times']
        
        report = {
            'target_url': self.target_url,
            'test_duration_seconds': total_time,
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'success_rate': (self.metrics['successful_requests'] / self.metrics['total_requests'] * 100),
            'requests_per_second': actual_rps,
            'response_time_metrics': {
                'average': statistics.mean(response_times) if response_times else 0,
                'median': statistics.median(response_times) if response_times else 0,
                'p95': np.percentile(response_times, 95) if response_times else 0,
                'p99': np.percentile(response_times, 99) if response_times else 0,
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0
            },
            'start_time': datetime.fromtimestamp(self.metrics['start_time']).isoformat(),
            'end_time': datetime.fromtimestamp(self.metrics['end_time']).isoformat()
        }
        
        self.print_report(report)
        self.plot_metrics()
        
        return report
    
    def print_report(self, report):
        """Красивый вывод отчета"""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
        print("="*60)
        print(f"🎯 Цель: {report['target_url']}")
        print(f"⏱️ Длительность: {report['test_duration_seconds']:.2f} сек")
        print(f"📨 Всего запросов: {report['total_requests']}")
        print(f"✅ Успешных: {report['successful_requests']}")
        print(f"❌ Ошибок: {report['failed_requests']}")
        print(f"📈 Успешность: {report['success_rate']:.2f}%")
        print(f"🚀 RPS: {report['requests_per_second']:.2f}")
        print("\n⏳ ВРЕМЯ ОТВЕТА:")
        print(f"   Среднее: {report['response_time_metrics']['average']:.3f}с")
        print(f"   Медиана: {report['response_time_metrics']['median']:.3f}с")
        print(f"   P95: {report['response_time_metrics']['p95']:.3f}с")
        print(f"   P99: {report['response_time_metrics']['p99']:.3f}с")
        print(f"   Min: {report['response_time_metrics']['min']:.3f}с")
        print(f"   Max: {report['response_time_metrics']['max']:.3f}с")
        print("="*60)
    
    def plot_metrics(self):
        """Визуализация метрик"""
        if not self.results:
            return
            
        # Группировка по секундам для графика RPS
        df = pd.DataFrame(self.results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['second'] = df['timestamp'].dt.floor('S')
        
        rps_data = df.groupby('second').size()
        
        plt.figure(figsize=(12, 8))
        
        # График RPS
        plt.subplot(2, 2, 1)
        plt.plot(rps_data.index, rps_data.values)
        plt.title('Запросов в секунду (RPS)')
        plt.xlabel('Время')
        plt.ylabel('RPS')
        plt.xticks(rotation=45)
        
        # График времени ответа
        plt.subplot(2, 2, 2)
        plt.hist(self.metrics['response_times'], bins=50, alpha=0.7)
        plt.title('Распределение времени ответа')
        plt.xlabel('Время (сек)')
        plt.ylabel('Частота')
        
        # График успешности запросов
        plt.subplot(2, 2, 3)
        status_counts = df['status'].value_counts()
        plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
        plt.title('Статусы ответов')
        
        # Кумулятивный график запросов
        plt.subplot(2, 2, 4)
        cumulative_requests = range(1, len(self.metrics['response_times']) + 1)
        plt.plot(cumulative_requests, self.metrics['response_times'])
        plt.title('Время ответа по запросам')
        plt.xlabel('Номер запроса')
        plt.ylabel('Время ответа (сек)')
        
        plt.tight_layout()
        plt.savefig('load_test_report.png', dpi=300, bbox_inches='tight')
        print("📊 Графики сохранены в load_test_report.png")

class ProgressiveLoadTester:
    """Постепенное увеличение нагрузки"""
    
    def __init__(self, target_url):
        self.target_url = target_url
    
    async def run_progressive_test(self):
        """Запуск прогрессивного теста"""
        load_levels = [
            {'rps': 200_000, 'duration': 30_000_000, 'workers': 1200_0000},
            {'rps': 200_000, 'duration': 30_000_000, 'workers': 200_000},
            {'rps': 200_000, 'duration': 30_000_000, 'workers': 200_000},
            {'rps': 200_000, 'duration': 30_000_000, 'workers': 200_000},
            {'rps': 200_000, 'duration': 30_000_000, 'workers': 200_000},
        ]
        
        print("🎚️ ЗАПУСК ПРОГРЕССИВНОГО ТЕСТИРОВАНИЯ")
        print("="*50)
        
        for level in load_levels:
            print(f"\n🚀 Уровень: {level['rps']} RPS, {level['duration']} сек")
            
            tester = ProfessionalLoadTester(
                self.target_url,
                max_workers=level['workers'],
                test_duration=level['duration']
            )
            
            report = await tester.run_load_test(target_rps=level['rps'])
            
            # Проверка точки отказа
            if report['success_rate'] < 95:
                print(f"⚠️ ДОСТИГНУТА ТОЧКА ОТКАЗА НА {level['rps']} RPS")
                break

# Дополнительные утилиты
def pre_test_analysis(target_url):
    """Предварительный анализ цели"""
    print("🔍 ПРЕДВАРИТЕЛЬНЫЙ АНАЛИЗ")
    
    try:
        response = requests.get(target_url, timeout=10)
        
        print(f"✅ Сайт доступен: HTTP {response.status_code}")
        print(f"📄 Сервер: {response.headers.get('Server', 'Неизвестно')}")
        print(f"⏱️ Первоначальное время ответа: {response.elapsed.total_seconds():.3f}с")
        
        # Проверка безопасности
        security_headers = ['X-Frame-Options', 'X-Content-Type-Options', 'Strict-Transport-Security']
        for header in security_headers:
            if header in response.headers:
                print(f"🛡️ {header}: {response.headers[header]}")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")

# Главная функция
async def main():
    """Основная функция запуска"""
    
    # ⚠️ ВАЖНО: Используйте ТОЛЬКО с разрешения владельца!
    TARGET_URL = "https://www.engineeredarts.net/"  # Тестовый URL для демонстрации
    
    print("🧪 СИСТЕМА ЛЕГАЛЬНОГО НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("⚠️  Используйте только с разрешения владельца сайта!")
    print("="*60)
    
    # Предварительный анализ
    pre_test_analysis(TARGET_URL)
    
    # Выбор типа теста
    test_type = input("\nВыберите тип теста (1-Базовый, 2-Прогрессивный): ")
    
    if test_type == "1":
        # Базовый нагрузочный тест
        tester = ProfessionalLoadTester(
            target_url=TARGET_URL,
            max_workers=50_000_000,
            test_duration=6000000  # 1 минута для демонстрации
        )
        await tester.run_load_test(target_rps=50)
        
    elif test_type == "2":
        # Прогрессивный тест
        progressive_tester = ProgressiveLoadTester(TARGET_URL)
        await progressive_tester.run_progressive_test()
    
    print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("📄 Подробный отчет сгенерирован")

# Запуск
if __name__ == "__main__":
    import numpy as np  # Для перцентилей
    
    # Проверка разрешения
    print("ПРЕДУПРЕЖДЕНИЕ: Этот инструмент предназначен только для легального использования.")
    print("Вы имеете письменное разрешение владельца целевого сайта? (y/N)")
    
    confirmation = input().lower()
    if confirmation == 'y':
        asyncio.run(main())
    else:
        print("❌ Тестирование отменено. Получите разрешение перед использованием.")
