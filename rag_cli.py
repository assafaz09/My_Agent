#!/usr/bin/env python3
"""
RAG Management CLI for Assaf's Agent

Command-line interface to manage and monitor the RAG system.
"""

import asyncio
import argparse
import json
import sys
from typing import List

from app.services.rag_manager import RAGManager

class RAGCLI:
    def __init__(self):
        self.rag_manager = RAGManager()
    
    async def stats(self):
        """Show RAG system statistics"""
        print("📊 RAG System Statistics")
        print("=" * 50)
        
        stats = await self.rag_manager.get_rag_stats()
        
        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        print(f"📄 Total Documents: {stats['total_documents']}")
        print(f"🔍 Total Vector Points: {stats['total_points']}")
        print(f"📏 Vector Size: {stats['vector_size']}")
        print(f"📐 Distance Metric: {stats['distance_metric']}")
        print(f"🚀 Enhanced RAG: {'✅ Initialized' if stats['enhanced_rag_initialized'] else '❌ Not Initialized'}")
        print(f"💾 Storage Size: {stats['storage_size_mb']} MB")
        print(f"📅 Last Updated: {stats['last_updated']}")
        
        print("\n📁 Documents by Type:")
        for doc_type, count in stats['documents_by_type'].items():
            print(f"  {doc_type}: {count}")
    
    async def test_search(self, queries: List[str] = None):
        """Test search performance"""
        if not queries:
            queries = [
                "What are Assaf's technical skills?",
                "Tell me about Assaf's experience",
                "What projects has Assaf worked on?",
                "Assaf's communication style",
                "Assaf's goals and aspirations"
            ]
        
        print("🔍 Search Performance Test")
        print("=" * 50)
        
        results = await self.rag_manager.test_search_performance(queries)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        for query, metrics in results.items():
            print(f"\n📝 Query: {query}")
            print("-" * 40)
            
            for method, data in metrics.items():
                print(f"  {method.replace('_', ' ').title()}:")
                print(f"    Results: {data['results_count']}")
                print(f"    Avg Score: {data['avg_score']:.3f}")
                print(f"    Time: {data['time_seconds']:.3f}s")
    
    async def analyze_gaps(self, topics: List[str] = None):
        """Analyze knowledge gaps"""
        if not topics:
            topics = [
                "technical skills",
                "personal background",
                "work experience",
                "education",
                "achievements",
                "communication style",
                "goals and aspirations"
            ]
        
        print("🔍 Knowledge Gap Analysis")
        print("=" * 50)
        
        gaps = await self.rag_manager.analyze_knowledge_gaps(topics)
        
        if "error" in gaps:
            print(f"❌ Error: {gaps['error']}")
            return
        
        for topic, analysis in gaps.items():
            coverage = analysis['coverage']
            icon = "✅" if coverage == "good" else "⚠️" if coverage in ["limited", "low_quality"] else "❌"
            
            print(f"\n{icon} {topic.title()}: {coverage.upper()}")
            print(f"💡 {analysis['suggestion']}")
            
            if 'existing_docs' in analysis:
                print(f"📄 Existing Documents: {analysis['existing_docs']}")
            if 'avg_relevance' in analysis:
                print(f"📊 Avg Relevance: {analysis['avg_relevance']:.3f}")
    
    async def optimize_thresholds(self):
        """Optimize search thresholds"""
        print("🎯 Search Threshold Optimization")
        print("=" * 50)
        
        test_queries = [
            "Assaf's skills",
            "work experience",
            "projects",
            "background"
        ]
        
        results = await self.rag_manager.optimize_search_thresholds(test_queries)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print("\n📊 Threshold Test Results:")
        for threshold, metrics in results['threshold_tests'].items():
            print(f"  Threshold {threshold}:")
            print(f"    Avg Results: {metrics['avg_results_per_query']:.1f}")
            print(f"    Zero Results Rate: {metrics['zero_results_rate']:.1%}")
        
        print(f"\n🎯 Optimal Threshold: {results['optimal_threshold']}")
        print(f"💡 {results['recommendation']}")
    
    async def rebuild_index(self):
        """Rebuild the RAG index"""
        print("🔄 Rebuilding RAG Index")
        print("=" * 50)
        
        result = await self.rag_manager.rebuild_index()
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"✅ Rebuild Complete!")
        print(f"📄 Documents Processed: {result['documents_processed']}")
        print(f"⏱️  Rebuild Time: {result['rebuild_time_seconds']:.3f}s")
        print(f"🚀 Enhanced RAG: {'✅ Initialized' if result['enhanced_rag_initialized'] else '❌ Failed'}")
    
    async def export_summary(self):
        """Export knowledge summary"""
        print("📋 Knowledge Summary Export")
        print("=" * 50)
        
        summary = await self.rag_manager.export_knowledge_summary()
        
        if "error" in summary:
            print(f"❌ Error: {summary['error']}")
            return
        
        print(f"📄 Total Documents: {summary['total_documents']}")
        
        print("\n📁 Document Details:")
        for i, doc in enumerate(summary['document_summary'][:10], 1):  # Show first 10
            print(f"\n{i}. {doc['filename']} ({doc['file_type']})")
            print(f"   Length: {doc['content_length']} chars")
            print(f"   Preview: {doc['preview']}")
        
        if len(summary['document_summary']) > 10:
            print(f"\n... and {len(summary['document_summary']) - 10} more documents")
        
        print(f"\n📝 Content Overview:")
        print(summary['content_overview'])
        
        # Save to file
        with open('knowledge_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Summary saved to: knowledge_summary.json")

async def main():
    parser = argparse.ArgumentParser(description="RAG Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show RAG system statistics')
    
    # Test search command
    test_parser = subparsers.add_parser('test', help='Test search performance')
    test_parser.add_argument('--queries', nargs='*', help='Test queries to use')
    
    # Gap analysis command
    gap_parser = subparsers.add_parser('gaps', help='Analyze knowledge gaps')
    gap_parser.add_argument('--topics', nargs='*', help='Topics to analyze')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Optimize search thresholds')
    
    # Rebuild command
    subparsers.add_parser('rebuild', help='Rebuild RAG index')
    
    # Export command
    subparsers.add_parser('export', help='Export knowledge summary')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = RAGCLI()
    
    try:
        if args.command == 'stats':
            await cli.stats()
        elif args.command == 'test':
            await cli.test_search(args.queries)
        elif args.command == 'gaps':
            await cli.analyze_gaps(args.topics)
        elif args.command == 'optimize':
            await cli.optimize_thresholds()
        elif args.command == 'rebuild':
            await cli.rebuild_index()
        elif args.command == 'export':
            await cli.export_summary()
        
        print("\n✅ Command completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
