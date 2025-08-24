/**
 * Newsletter Statistics Card Component
 *
 * Displays enhanced newsletter metrics including quality scores,
 * citation compliance, content length metrics, and cost tracking.
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  TrendingUp,
  FileText,
  DollarSign,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Clock,
  Link
} from 'lucide-react';


interface NewsletterStats {
  period_days: number;
  total_newsletters: number;
  newsletter_types: {
    daily: number;
    weekly: number;
  };
  status_breakdown: Record<string, number>;
  quality_metrics: {
    average_quality_score: number;
    newsletters_with_scores: number;
    citation_metrics: {
      average_citations: number;
      newsletters_with_citations: number;
      citation_compliance_rate: number;
      minimum_citations_required: number;
    };
    content_length_metrics: {
      average_word_count: number;
      newsletters_analyzed: number;
    };
  };
  cost_metrics: {
    total_generation_cost: number;
    average_cost_per_newsletter: number;
    newsletters_with_cost_data: number;
  };
  quality_trends: Array<{
    date: string;
    quality_score: number;
    newsletter_id: number;
    type: string;
  }>;
  recent_newsletters: Array<{
    id: number;
    title: string;
    type: string;
    status: string;
    generation_date: string;
    quality_score: number | null;
  }>;
  timestamp: string;
}

interface NewsletterStatsCardProps {
  days?: number;
  className?: string;
}

export function NewsletterStatsCard({ days = 30, className }: NewsletterStatsCardProps) {
  const [stats, setStats] = useState<NewsletterStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/newsletters/stats?days=${days}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch newsletter stats: ${response.statusText}`);
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        console.error('Error fetching newsletter stats:', err);
        setError(err instanceof Error ? err.message : 'Failed to load newsletter statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [days]);

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Newsletter Statistics
          </CardTitle>
          <CardDescription>Loading newsletter metrics...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-4 bg-muted rounded animate-pulse" />
            <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
            <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !stats) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Newsletter Statistics
          </CardTitle>
          <CardDescription>Failed to load statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error || 'No data available'}</p>
        </CardContent>
      </Card>
    );
  }

  const qualityScoreColor = stats.quality_metrics.average_quality_score >= 0.8
    ? 'text-green-600'
    : stats.quality_metrics.average_quality_score >= 0.6
    ? 'text-yellow-600'
    : 'text-red-600';

  const citationComplianceColor = stats.quality_metrics.citation_metrics.citation_compliance_rate >= 0.8
    ? 'text-green-600'
    : stats.quality_metrics.citation_metrics.citation_compliance_rate >= 0.6
    ? 'text-yellow-600'
    : 'text-red-600';

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Newsletter Statistics
        </CardTitle>
        <CardDescription>
          Last {stats.period_days} days • {stats.total_newsletters} newsletters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Newsletter Types */}
        <div>
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Newsletter Types
          </h4>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <Badge variant="outline">Daily</Badge>
              <span className="text-sm text-muted-foreground">{stats.newsletter_types.daily}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">Weekly</Badge>
              <span className="text-sm text-muted-foreground">{stats.newsletter_types.weekly}</span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Quality Metrics */}
        <div>
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Quality Metrics
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Average Quality Score</span>
              <span className={`text-sm font-medium ${qualityScoreColor}`}>
                {stats.quality_metrics.average_quality_score.toFixed(2)}
              </span>
            </div>
            <Progress
              value={stats.quality_metrics.average_quality_score * 100}
              className="h-2"
            />

            <div className="flex items-center justify-between">
              <span className="text-sm">Citation Compliance</span>
              <span className={`text-sm font-medium ${citationComplianceColor}`}>
                {(stats.quality_metrics.citation_metrics.citation_compliance_rate * 100).toFixed(1)}%
              </span>
            </div>
            <Progress
              value={stats.quality_metrics.citation_metrics.citation_compliance_rate * 100}
              className="h-2"
            />
          </div>
        </div>

        <Separator />

        {/* Content Metrics */}
        <div>
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Link className="h-4 w-4" />
            Content Metrics
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Avg Citations</div>
              <div className="font-medium">
                {stats.quality_metrics.citation_metrics.average_citations.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Avg Word Count</div>
              <div className="font-medium">
                {stats.quality_metrics.content_length_metrics.average_word_count.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Cost Metrics */}
        <div>
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Cost Metrics
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Total Cost</div>
              <div className="font-medium">
                ${stats.cost_metrics.total_generation_cost.toFixed(4)}
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Avg per Newsletter</div>
              <div className="font-medium">
                ${stats.cost_metrics.average_cost_per_newsletter.toFixed(4)}
              </div>
            </div>
          </div>
        </div>

        {/* Status Breakdown */}
        {Object.keys(stats.status_breakdown).length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Status Breakdown
              </h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(stats.status_breakdown).map(([status, count]) => (
                  <Badge key={status} variant="secondary" className="text-xs">
                    {status}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Last Updated */}
        <div className="text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="h-3 w-3" />
          Updated: {new Date(stats.timestamp).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}
