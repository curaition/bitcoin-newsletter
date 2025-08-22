/**
 * Newsletter Generation Page
 *
 * Interface for manually triggering newsletter generation with options
 * for daily/weekly newsletters and force generation.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
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
  Info,
  Search,
  Brain,
  PenTool,
  Save
} from 'lucide-react';
import { useGenerateNewsletter, useNewsletterStats } from '@/hooks/api/useNewsletters';
import type { NewsletterType, GenerationProgress } from '../../../../shared/types/api';
import { NEWSLETTER_TYPE_OPTIONS } from '../../../../shared/types/api';
import { apiClient } from '@/services/api/client';

export function NewsletterGeneratePage() {
  const [selectedType, setSelectedType] = useState<NewsletterType>('DAILY');
  const [forceGeneration, setForceGeneration] = useState(false);
  const [generationState, setGenerationState] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [generationResult, setGenerationResult] = useState<any>(null);

  // Newsletter generation mutation
  const generateMutation = useGenerateNewsletter();

  // Newsletter stats for context
  const { data: stats } = useNewsletterStats();

  // Poll for progress updates
  const { data: progressData, error: progressError } = useQuery({
    queryKey: ['newsletter-progress', taskId],
    queryFn: () => apiClient.getGenerationProgress(taskId!),
    enabled: taskId !== null && generationState === 'generating',
    refetchInterval: 2000, // Poll every 2 seconds
    retry: 3,
  });

  // Handle progress updates
  useEffect(() => {
    if (progressData) {
      if (progressData.status === 'complete') {
        setGenerationState('complete');
        // Set the generation result for the completion display
        setGenerationResult({
          task_id: taskId,
          newsletter_type: selectedType,
          status: 'complete',
          force_generation: forceGeneration
        });
      } else if (progressData.status === 'failed') {
        setGenerationState('error');
      }
    }
  }, [progressData, taskId, selectedType, forceGeneration]);

  const handleGenerate = async () => {
    try {
      setGenerationState('generating');
      const result = await generateMutation.mutateAsync({
        newsletter_type: selectedType,
        force_generation: forceGeneration
      });
      setTaskId(result.task_id);
    } catch (error) {
      console.error('Failed to generate newsletter:', error);
      setGenerationState('error');
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

  const getStepIcon = (step: string, isActive: boolean, isComplete: boolean) => {
    const iconClass = `h-4 w-4 ${isActive ? 'text-blue-500' : isComplete ? 'text-green-500' : 'text-gray-400'}`;

    switch (step) {
      case 'selection': return <Search className={iconClass} />;
      case 'synthesis': return <Brain className={iconClass} />;
      case 'writing': return <PenTool className={iconClass} />;
      case 'storage': return <Save className={iconClass} />;
      default: return <FileText className={iconClass} />;
    }
  };

  // Show progress interface during generation
  if (generationState === 'generating' && progressData) {
    return <NewsletterGenerationProgress progress={progressData} getStepIcon={getStepIcon} />;
  }

  // Show completion interface
  if (generationState === 'complete') {
    return <NewsletterGenerationComplete taskId={taskId} progressData={progressData} onRetry={() => setGenerationState('idle')} />;
  }

  // Show error interface
  if (generationState === 'error') {
    return <NewsletterGenerationError error={progressError} onRetry={() => setGenerationState('idle')} />;
  }

  if (false) { // Disable old success result display
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

// Progress visualization component
function NewsletterGenerationProgress({ progress, getStepIcon }: { progress: GenerationProgress, getStepIcon: any }) {
  const steps = [
    { key: 'selection', title: 'Story Selection', description: 'Analyzing articles and selecting the most revealing stories' },
    { key: 'synthesis', title: 'Pattern Analysis', description: 'Identifying connections and market patterns' },
    { key: 'writing', title: 'Content Generation', description: 'Creating compelling newsletter content with citations' },
    { key: 'storage', title: 'Finalizing', description: 'Storing and preparing newsletter' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <div>
          <h1 className="text-2xl font-bold">Generating Newsletter</h1>
          <p className="text-muted-foreground">
            Creating your {progress.step_details.articles_count ? `newsletter from ${progress.step_details.articles_count} articles` : 'newsletter'}...
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            <span>Newsletter Generation in Progress</span>
          </CardTitle>
          <CardDescription>
            {progress.step_details.step_description || progress.step_details.status}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{Math.round(progress.overall_progress * 100)}%</span>
            </div>
            <Progress value={progress.overall_progress * 100} className="h-2" />
          </div>

          {/* Step-by-step Progress */}
          <div className="space-y-4">
            {steps.map((step, index) => {
              const isActive = progress.current_step === step.key;
              const isComplete = steps.findIndex(s => s.key === progress.current_step) > index;

              return (
                <div key={step.key} className={`flex items-start space-x-3 p-3 rounded-lg ${isActive ? 'bg-blue-50 border border-blue-200' : isComplete ? 'bg-green-50 border border-green-200' : 'bg-gray-50'}`}>
                  <div className="flex-shrink-0 mt-1">
                    {getStepIcon(step.key, isActive, isComplete)}
                  </div>
                  <div className="flex-1">
                    <h4 className={`font-medium ${isActive ? 'text-blue-900' : isComplete ? 'text-green-900' : 'text-gray-700'}`}>
                      {step.title}
                    </h4>
                    <p className={`text-sm ${isActive ? 'text-blue-700' : isComplete ? 'text-green-700' : 'text-gray-500'}`}>
                      {step.description}
                    </p>

                    {/* Step-specific progress */}
                    {isActive && (
                      <div className="mt-2 space-y-1">
                        <Progress value={progress.step_progress * 100} className="h-1" />
                        <div className="flex justify-between text-xs text-blue-600">
                          <span>{progress.step_details.status}</span>
                          <span>{Math.round(progress.step_progress * 100)}%</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Step completion indicator */}
                  {isComplete && (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Quality Metrics */}
          {(progress.step_details.quality_score || progress.step_details.citation_count || progress.step_details.selected_count) && (
            <div className="space-y-2">
              <h4 className="font-medium">Quality Metrics</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                {progress.step_details.selected_count && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Stories Selected:</span>
                    <Badge variant="secondary">{progress.step_details.selected_count}</Badge>
                  </div>
                )}
                {progress.step_details.quality_score && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Quality Score:</span>
                    <Badge variant="secondary">{Math.round(progress.step_details.quality_score * 100)}%</Badge>
                  </div>
                )}
                {progress.step_details.citation_count && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Citations:</span>
                    <Badge variant="secondary">{progress.step_details.citation_count}</Badge>
                  </div>
                )}
                {progress.step_details.word_count && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Word Count:</span>
                    <Badge variant="secondary">{progress.step_details.word_count.toLocaleString()}</Badge>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Intermediate Results Preview */}
          {progress.intermediate_results && (
            <div className="space-y-4">
              <h4 className="font-medium">Preview</h4>

              {/* Selected Stories Preview */}
              {progress.intermediate_results.selection && (
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-muted-foreground">Selected Stories</h5>
                  <div className="space-y-2">
                    {progress.intermediate_results.selection.selected_stories.slice(0, 3).map((story, index) => (
                      <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="font-medium">{story.title}</div>
                        <div className="text-muted-foreground">{story.publisher} • Signal: {story.signal_strength.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Themes Preview */}
              {progress.intermediate_results.synthesis && (
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-muted-foreground">Key Themes</h5>
                  <div className="flex flex-wrap gap-1">
                    {progress.intermediate_results.synthesis.primary_themes.map((theme, index) => (
                      <Badge key={index} variant="outline" className="text-xs">{theme}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Newsletter Preview */}
              {progress.intermediate_results.writing && (
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-muted-foreground">Newsletter Preview</h5>
                  <div className="p-3 bg-gray-50 rounded">
                    <div className="font-medium text-sm">{progress.intermediate_results.writing.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {progress.intermediate_results.writing.executive_summary[0]}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Estimated Completion */}
          {progress.estimated_completion && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Estimated completion: {new Date(progress.estimated_completion).toLocaleTimeString()}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Completion component
function NewsletterGenerationComplete({ taskId, progressData, onRetry }: { taskId: string | null, progressData: any, onRetry: () => void }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/newsletters">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Newsletters
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Newsletter Generation Complete</h1>
          <p className="text-muted-foreground">Your newsletter has been generated successfully</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span>Generation Complete</span>
          </CardTitle>
          <CardDescription>
            Newsletter generation completed successfully
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-medium">Task ID</label>
              <p className="text-sm font-mono bg-muted p-2 rounded">{taskId}</p>
            </div>
            {progressData?.step_details?.newsletter_id && (
              <div>
                <label className="text-sm font-medium">Newsletter ID</label>
                <p className="text-sm">{progressData.step_details.newsletter_id}</p>
              </div>
            )}
          </div>

          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Your newsletter has been generated and is ready for review. You can find it in the newsletters list.
            </AlertDescription>
          </Alert>

          <div className="flex space-x-2">
            <Button asChild>
              <Link to="/newsletters">
                View All Newsletters
              </Link>
            </Button>
            <Button variant="outline" onClick={onRetry}>
              Generate Another
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Error component
function NewsletterGenerationError({ error, onRetry }: { error: any, onRetry: () => void }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/newsletters">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Newsletters
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Newsletter Generation Failed</h1>
          <p className="text-muted-foreground">There was an error generating your newsletter</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span>Generation Failed</span>
          </CardTitle>
          <CardDescription>
            Newsletter generation encountered an error
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error?.message || 'An unexpected error occurred during newsletter generation. Please try again.'}
            </AlertDescription>
          </Alert>

          <div className="flex space-x-2">
            <Button onClick={onRetry}>
              Try Again
            </Button>
            <Button variant="outline" asChild>
              <Link to="/newsletters">
                Back to Newsletters
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
