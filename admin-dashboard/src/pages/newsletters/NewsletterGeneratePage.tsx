/**
 * Newsletter Generation Page
 *
 * Interface for manually triggering newsletter generation with options
 * for daily/weekly newsletters and force generation.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
// Checkbox component temporarily removed - using basic HTML checkbox
// Select component temporarily removed - using basic HTML select
import {
  ArrowLeft,

  FileText,
  Zap,
  Clock,
  AlertTriangle,
  Loader2,
  CheckCircle,
  Info
} from 'lucide-react';
import { useGenerateNewsletter, useNewsletterStats } from '@/hooks/api/useNewsletters';
import type { NewsletterType } from '../../../../shared/types/api';
import { NEWSLETTER_TYPE_OPTIONS } from '../../../../shared/types/api';

export function NewsletterGeneratePage() {

  const [selectedType, setSelectedType] = useState<NewsletterType>('DAILY');
  const [forceGeneration, setForceGeneration] = useState(false);
  const [generationResult, setGenerationResult] = useState<any>(null);

  // Newsletter generation mutation
  const generateMutation = useGenerateNewsletter();

  // Newsletter stats for context
  const { data: stats } = useNewsletterStats();

  const handleGenerate = async () => {
    try {
      const result = await generateMutation.mutateAsync({
        newsletter_type: selectedType,
        force_generation: forceGeneration
      });
      setGenerationResult(result);
    } catch (error) {
      console.error('Failed to generate newsletter:', error);
    }
  };

  const getTypeDescription = (type: NewsletterType) => {
    switch (type) {
      case 'DAILY':
        return 'Generates a newsletter from articles analyzed in the past 24 hours. Requires at least 10 analyzed articles.';
      case 'WEEKLY':
        return 'Generates a newsletter from daily newsletters published in the past 7 days. Requires at least 3 daily newsletters.';
      default:
        return '';
    }
  };

  const getTypeRequirements = (type: NewsletterType) => {
    switch (type) {
      case 'DAILY':
        return {
          requirement: 'Minimum 10 analyzed articles from past 24 hours',
          schedule: 'Automatically generated daily at 6:00 AM UTC'
        };
      case 'WEEKLY':
        return {
          requirement: 'Minimum 3 daily newsletters from past 7 days',
          schedule: 'Automatically generated Monday at 8:00 AM UTC'
        };
      default:
        return { requirement: '', schedule: '' };
    }
  };

  // const getRecentCount = (type: NewsletterType) => { // Temporarily unused
  //   if (!stats) return 0;
  //   return type === 'DAILY' ? stats.newsletter_types.daily : stats.newsletter_types.weekly;
  // };

  if (generationResult) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/newsletters">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Newsletters
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Newsletter Generation</h1>
            <p className="text-muted-foreground">Generation request submitted</p>
          </div>
        </div>

        {/* Success Result */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span>Generation Started</span>
            </CardTitle>
            <CardDescription>
              Your newsletter generation request has been queued successfully
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Task ID</label>
                <p className="text-sm font-mono bg-muted p-2 rounded">{generationResult.task_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Newsletter Type</label>
                <p className="text-sm">{generationResult.newsletter_type}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <Badge variant="secondary">{generationResult.status}</Badge>
              </div>
              <div>
                <label className="text-sm font-medium">Force Generation</label>
                <p className="text-sm">{generationResult.force_generation ? 'Yes' : 'No'}</p>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Newsletter generation typically takes 2-5 minutes. You can monitor progress in the newsletters list or check back later.
              </AlertDescription>
            </Alert>

            <div className="flex space-x-2">
              <Button asChild>
                <Link to="/newsletters">
                  View All Newsletters
                </Link>
              </Button>
              <Button variant="outline" onClick={() => setGenerationResult(null)}>
                Generate Another
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/newsletters">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Newsletters
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Generate Newsletter</h1>
          <p className="text-muted-foreground">Manually trigger newsletter generation</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Generation Form */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Newsletter Generation Options</CardTitle>
              <CardDescription>
                Configure your newsletter generation parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Newsletter Type Selection */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Newsletter Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value as NewsletterType)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  {NEWSLETTER_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-muted-foreground">
                  {getTypeDescription(selectedType)}
                </p>
              </div>

              <Separator />

              {/* Requirements */}
              <div className="space-y-3">
                <h4 className="font-medium">Requirements & Schedule</h4>
                <div className="space-y-2">
                  <div className="flex items-start space-x-2">
                    <FileText className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">{getTypeRequirements(selectedType).requirement}</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Clock className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">{getTypeRequirements(selectedType).schedule}</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Force Generation Option */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="force-generation"
                    checked={forceGeneration}
                    onChange={(e) => setForceGeneration(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label htmlFor="force-generation" className="text-sm font-medium">
                    Force Generation
                  </label>
                </div>
                <p className="text-sm text-muted-foreground">
                  Generate newsletter even if minimum requirements are not met. This may result in lower quality content.
                </p>
                {forceGeneration && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      Force generation bypasses quality checks and may produce newsletters with insufficient content.
                    </AlertDescription>
                  </Alert>
                )}
              </div>

              <Separator />

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
                className="w-full"
                size="lg"
              >
                {generateMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                Generate {selectedType} Newsletter
              </Button>

              {generateMutation.error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Failed to start newsletter generation. Please try again.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          {/* Recent Activity */}
          {stats && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Newsletter generation statistics (past 30 days)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Total Newsletters</span>
                    <span className="text-sm font-medium">{stats.total_newsletters}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Daily Newsletters</span>
                    <span className="text-sm font-medium">{stats.newsletter_types.daily}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Weekly Newsletters</span>
                    <span className="text-sm font-medium">{stats.newsletter_types.weekly}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Avg Quality Score</span>
                    <span className="text-sm font-medium">
                      {stats.quality_metrics.average_quality_score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Generation Tips */}
          <Card>
            <CardHeader>
              <CardTitle>Generation Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm space-y-2">
                <p>• Daily newsletters work best with 10+ analyzed articles</p>
                <p>• Weekly newsletters synthesize insights from daily newsletters</p>
                <p>• Generation typically takes 2-5 minutes</p>
                <p>• Quality scores above 0.7 are recommended for publishing</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
