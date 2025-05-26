#!/usr/bin/env python3
"""
🚀 OpenMedia News Monitor
Monitor simple y eficaz para sitios de noticias chilenos.

Uso: python run_monitor.py
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add the crawlers directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from crawlers.news_monitor import NewsMonitor


async def main():
    """Ejecutar el News Monitor."""
    print("🚀 OpenMedia News Monitor")
    print("=" * 50)
    print("📰 Monitoreando sitios de noticias chilenos...")
    print("⏹️  Presiona Ctrl+C para detener")
    print()
    
    monitor = NewsMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo monitor...")
        
        # Cleanup
        if hasattr(monitor, 'kafka_producer') and monitor.kafka_producer:
            monitor.kafka_producer.close()
        if hasattr(monitor, 'session') and monitor.session:
            monitor.session.close()
            
        print("👋 Monitor detenido correctamente")
        
        # Show final stats
        stats = monitor.get_stats()
        print(f"\n📊 Estadísticas finales:")
        print(f"   • Artículos encontrados: {stats['articles_found']}")
        print(f"   • Artículos procesados: {stats['articles_processed']}")
        print(f"   • Errores: {stats['errors']}")
        print(f"   • Tiempo de ejecución: {stats['runtime_seconds']:.1f}s")


if __name__ == '__main__':
    asyncio.run(main()) 