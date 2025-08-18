import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Pause, Square, Trash2, Plus, RefreshCw, Eye } from 'lucide-react';
import { fetchScrapingJobs, createScrapingJob, startScrapingJob, stopScrapingJob, pauseScrapingJob, deleteScrapingJob, fetchScrapingSources } from '../../services/api';
import { formatTimestamp, getStatusColor } from '../../services/api';

const JobStatusBadge = ({ status }) => {
  const color = getStatusColor(status);
  const colorClasses = {
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
    blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
  };

  return (
    <Badge className={`${colorClasses[color]} border`}>
      {status}
    </Badge>
  );
};

const CreateJobDialog = ({ onCreateJob }) => {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    job_name: '',
    source_names: [],
    max_questions_per_source: 50,
    target_categories: [],
    priority_level: 'medium'
  });

  const { data: sources } = useQuery({
    queryKey: ['scrapingSources'],
    queryFn: fetchScrapingSources,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateJob(formData);
    setOpen(false);
    setFormData({
      job_name: '',
      source_names: [],
      max_questions_per_source: 50,
      target_categories: [],
      priority_level: 'medium'
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Create New Job
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-slate-900 border-slate-700 text-white sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Scraping Job</DialogTitle>
          <DialogDescription className="text-slate-400">
            Configure a new scraping job with your desired parameters.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="job_name">Job Name</Label>
            <Input
              id="job_name"
              value={formData.job_name}
              onChange={(e) => setFormData({ ...formData, job_name: e.target.value })}
              placeholder="Enter job name..."
              className="bg-slate-800 border-slate-600"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="sources">Source Selection</Label>
            <Select
              value={formData.source_names[0] || ''}
              onValueChange={(value) => setFormData({ ...formData, source_names: [value] })}
            >
              <SelectTrigger className="bg-slate-800 border-slate-600">
                <SelectValue placeholder="Select source..." />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-600">
                {sources?.map((source) => (
                  <SelectItem key={source.source_id} value={source.source_id}>
                    {source.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="max_questions">Max Questions per Source</Label>
            <Input
              id="max_questions"
              type="number"
              min="1"
              max="1000"
              value={formData.max_questions_per_source}
              onChange={(e) => setFormData({ ...formData, max_questions_per_source: parseInt(e.target.value) })}
              className="bg-slate-800 border-slate-600"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="categories">Target Categories</Label>
            <Select
              value={formData.target_categories[0] || ''}
              onValueChange={(value) => setFormData({ ...formData, target_categories: [value] })}
            >
              <SelectTrigger className="bg-slate-800 border-slate-600">
                <SelectValue placeholder="Select category..." />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-600">
                <SelectItem value="quantitative_aptitude">Quantitative Aptitude</SelectItem>
                <SelectItem value="logical_reasoning">Logical Reasoning</SelectItem>
                <SelectItem value="verbal_ability">Verbal Ability</SelectItem>
                <SelectItem value="computer_science">Computer Science</SelectItem>
                <SelectItem value="programming">Programming</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="priority">Priority Level</Label>
            <Select
              value={formData.priority_level}
              onValueChange={(value) => setFormData({ ...formData, priority_level: value })}
            >
              <SelectTrigger className="bg-slate-800 border-slate-600">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-600">
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              Create Job
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const JobActions = ({ job, onStartJob, onStopJob, onPauseJob, onDeleteJob }) => {
  const isRunning = job.status === 'RUNNING';
  const isPaused = job.status === 'PAUSED';
  const isCompleted = job.status === 'COMPLETED';

  return (
    <div className="flex items-center gap-2">
      {!isRunning && !isCompleted && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onStartJob(job.job_id)}
          className="h-8 w-8 p-0"
        >
          <Play className="w-4 h-4" />
        </Button>
      )}
      
      {isRunning && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPauseJob(job.job_id)}
          className="h-8 w-8 p-0"
        >
          <Pause className="w-4 h-4" />
        </Button>
      )}
      
      {(isRunning || isPaused) && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => onStopJob(job.job_id)}
          className="h-8 w-8 p-0"
        >
          <Square className="w-4 h-4" />
        </Button>
      )}
      
      <Button
        size="sm"
        variant="outline"
        onClick={() => onDeleteJob(job.job_id)}
        className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
      >
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  );
};

const JobManagementTab = () => {
  const queryClient = useQueryClient();

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['scrapingJobs'],
    queryFn: fetchScrapingJobs,
    refetchInterval: 5000,
  });

  const createJobMutation = useMutation({
    mutationFn: createScrapingJob,
    onSuccess: () => {
      queryClient.invalidateQueries(['scrapingJobs']);
    },
  });

  const startJobMutation = useMutation({
    mutationFn: startScrapingJob,
    onSuccess: () => {
      queryClient.invalidateQueries(['scrapingJobs']);
    },
  });

  const stopJobMutation = useMutation({
    mutationFn: stopScrapingJob,
    onSuccess: () => {
      queryClient.invalidateQueries(['scrapingJobs']);
    },
  });

  const pauseJobMutation = useMutation({
    mutationFn: pauseScrapingJob,
    onSuccess: () => {
      queryClient.invalidateQueries(['scrapingJobs']);
    },
  });

  const deleteJobMutation = useMutation({
    mutationFn: deleteScrapingJob,
    onSuccess: () => {
      queryClient.invalidateQueries(['scrapingJobs']);
    },
  });

  const handleCreateJob = (jobData) => {
    createJobMutation.mutate(jobData);
  };

  const handleStartJob = (jobId) => {
    startJobMutation.mutate(jobId);
  };

  const handleStopJob = (jobId) => {
    stopJobMutation.mutate(jobId);
  };

  const handlePauseJob = (jobId) => {
    pauseJobMutation.mutate(jobId);
  };

  const handleDeleteJob = (jobId) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      deleteJobMutation.mutate(jobId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Job Management Header */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-white">Scraping Jobs</CardTitle>
              <CardDescription className="text-blue-200">
                Manage and monitor your scraping operations
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => queryClient.invalidateQueries(['scrapingJobs'])}
                className="border-white/20"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <CreateJobDialog onCreateJob={handleCreateJob} />
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Jobs Table */}
      <Card className="bg-white/10 backdrop-blur-sm border-white/20">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-white/20">
                <TableHead className="text-white">Job Name</TableHead>
                <TableHead className="text-white">Status</TableHead>
                <TableHead className="text-white">Source</TableHead>
                <TableHead className="text-white">Progress</TableHead>
                <TableHead className="text-white">Created</TableHead>
                <TableHead className="text-white">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-blue-200">
                    Loading jobs...
                  </TableCell>
                </TableRow>
              ) : jobs && jobs.length > 0 ? (
                jobs.map((job) => (
                  <TableRow key={job.job_id} className="border-white/10">
                    <TableCell className="text-white font-medium">
                      {job.job_name}
                    </TableCell>
                    <TableCell>
                      <JobStatusBadge status={job.status} />
                    </TableCell>
                    <TableCell className="text-blue-200">
                      {job.source_names?.join(', ') || 'N/A'}
                    </TableCell>
                    <TableCell className="text-blue-200">
                      {job.progress_stats ? 
                        `${job.progress_stats.processed}/${job.progress_stats.total}` : 
                        '0/0'
                      }
                    </TableCell>
                    <TableCell className="text-blue-200">
                      {formatTimestamp(job.created_at)}
                    </TableCell>
                    <TableCell>
                      <JobActions
                        job={job}
                        onStartJob={handleStartJob}
                        onStopJob={handleStopJob}
                        onPauseJob={handlePauseJob}
                        onDeleteJob={handleDeleteJob}
                      />
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-blue-200">
                    No scraping jobs found. Create your first job to get started.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-green-500/20 border-green-500/30 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-white">
              {jobs?.filter(job => job.status === 'COMPLETED').length || 0}
            </div>
            <div className="text-sm text-green-200">Completed Jobs</div>
          </CardContent>
        </Card>

        <Card className="bg-blue-500/20 border-blue-500/30 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-white">
              {jobs?.filter(job => job.status === 'RUNNING').length || 0}
            </div>
            <div className="text-sm text-blue-200">Active Jobs</div>
          </CardContent>
        </Card>

        <Card className="bg-yellow-500/20 border-yellow-500/30 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-white">
              {jobs?.filter(job => job.status === 'PAUSED').length || 0}
            </div>
            <div className="text-sm text-yellow-200">Paused Jobs</div>
          </CardContent>
        </Card>

        <Card className="bg-purple-500/20 border-purple-500/30 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-white">
              {jobs?.length || 0}
            </div>
            <div className="text-sm text-purple-200">Total Jobs</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default JobManagementTab;