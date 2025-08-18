import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { 
  Search, BookOpen, Code, Users, Lightbulb, X, Calculator, Brain, 
  FileText, BarChart3, Building2, Trophy, Clock, Target, ChevronRight,
  TrendingUp, Flame, Star, Zap, Users2, MessageCircle, Award,
  Timer, BookMarked, PlayCircle, RotateCcw, Gamepad2, GraduationCap,
  PieChart, LineChart, Calendar, Bell, Sparkles, Download, Share2
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import QuestionPracticeSession from './QuestionPracticeSession';

const ComprehensiveAptitudeQuestions = () => {
  const [jobTitle, setJobTitle] = useState('');
  const [isTechnicalModalOpen, setIsTechnicalModalOpen] = useState(false);
  const [isAptitudeModalOpen, setIsAptitudeModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJobTitle, setSelectedJobTitle] = useState('');
  const [selectedAptitudeCategory, setSelectedAptitudeCategory] = useState('');
  const [selectedSubtopic, setSelectedSubtopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedLearningPath, setSelectedLearningPath] = useState('');
  const [selectedStudyMode, setSelectedStudyMode] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [isPracticeSessionActive, setIsPracticeSessionActive] = useState(false);

  const { toast } = useToast();

  // Smart Difficulty Progression System
  const smartLevels = [
    { 
      id: 'foundation', 
      name: 'Foundation', 
      description: '1st-2nd year students',
      questionCount: '20-30 questions',
      timeLimit: '30 minutes',
      icon: GraduationCap,
      color: 'bg-green-600'
    },
    { 
      id: 'placement-ready', 
      name: 'Placement Ready', 
      description: '3rd-4th year students',
      questionCount: '40-50 questions', 
      timeLimit: '45 minutes',
      icon: Trophy,
      color: 'bg-yellow-600'
    },
    { 
      id: 'campus-expert', 
      name: 'Campus Expert', 
      description: 'Top-tier company level',
      questionCount: '60+ questions',
      timeLimit: '60 minutes',
      icon: Award,
      color: 'bg-red-600'
    }
  ];

  // Time Management Coaching
  const timeManagementTips = {
    'Percentages': {
      avgTime: '45 seconds per question',
      tip: 'Use 10%, 20% method for quick calculations',
      shortcut: 'Remember: 12.5% = 1/8, 16.67% = 1/6',
      difficulty: 'Easy'
    },
    'Data Interpretation': {
      avgTime: '2-3 minutes per set',
      tip: 'Read questions first, then analyze chart',
      strategy: 'Skip complex calculations, focus on trends',
      difficulty: 'Hard'
    },
    'Blood Relations': {
      avgTime: '1-2 minutes per question',
      tip: 'Draw family tree for complex relations',
      shortcut: 'Learn standard relation patterns',
      difficulty: 'Medium'
    },
    'Profit & Loss': {
      avgTime: '60 seconds per question',
      tip: 'Use CP as base for calculations',
      shortcut: 'Remember: SP = CP + Profit or CP - Loss',
      difficulty: 'Medium'
    }
  };

  // Topic Priority System
  const getTopicPriority = (topic) => {
    const highPriority = ['Percentages', 'Profit & Loss', 'Blood Relations', 'Puzzles & Seating Arrangement', 'Reading Comprehension', 'Pie Charts'];
    const mediumPriority = ['Time & Work', 'Averages', 'Direction Sense', 'Coding-Decoding', 'Error Spotting', 'Bar Graphs'];
    
    if (highPriority.includes(topic)) {
      return { badge: 'HOT', color: 'bg-red-500', frequency: '90% of placement tests' };
    } else if (mediumPriority.includes(topic)) {
      return { badge: 'IMPORTANT', color: 'bg-orange-500', frequency: '60% of placement tests' };
    } else {
      return { badge: 'BONUS', color: 'bg-blue-500', frequency: '30% of placement tests' };
    }
  };

  // Enhanced Aptitude Categories with comprehensive data
  const aptitudeCategories = [
    {
      id: 'quantitative',
      title: 'Quantitative Aptitude',
      icon: Calculator,
      description: 'Mathematical problem-solving skills',
      color: 'bg-blue-600',
      successRate: '78%',
      avgScore: '72%',
      trending: true,
      totalQuestions: 450,
      subtopics: [
        { name: 'Percentages', priority: 'high', avgTime: '45s', successRate: '85%', difficulty: 'Easy', questions: 50 },
        { name: 'Profit & Loss', priority: 'high', avgTime: '60s', successRate: '72%', difficulty: 'Medium', questions: 45 },
        { name: 'Time, Speed & Distance', priority: 'medium', avgTime: '90s', successRate: '65%', difficulty: 'Medium', questions: 40 },
        { name: 'Time & Work', priority: 'medium', avgTime: '75s', successRate: '68%', difficulty: 'Medium', questions: 42 },
        { name: 'Averages', priority: 'medium', avgTime: '50s', successRate: '80%', difficulty: 'Easy', questions: 35 },
        { name: 'Number Systems', priority: 'low', avgTime: '40s', successRate: '75%', difficulty: 'Easy', questions: 38 },
        { name: 'Simplification', priority: 'high', avgTime: '30s', successRate: '90%', difficulty: 'Easy', questions: 55 },
        { name: 'HCF & LCM', priority: 'medium', avgTime: '55s', successRate: '70%', difficulty: 'Medium', questions: 32 },
        { name: 'Permutations & Combinations', priority: 'low', avgTime: '120s', successRate: '45%', difficulty: 'Hard', questions: 28 },
        { name: 'Probability', priority: 'low', avgTime: '100s', successRate: '50%', difficulty: 'Hard', questions: 25 }
      ]
    },
    {
      id: 'logical',
      title: 'Logical Reasoning',
      icon: Brain,
      description: 'Critical thinking and pattern recognition',
      color: 'bg-purple-600',
      successRate: '65%',
      avgScore: '68%',
      trending: false,
      totalQuestions: 380,
      subtopics: [
        { name: 'Blood Relations', priority: 'high', avgTime: '90s', successRate: '70%', difficulty: 'Medium', questions: 45 },
        { name: 'Direction Sense', priority: 'medium', avgTime: '60s', successRate: '75%', difficulty: 'Easy', questions: 40 },
        { name: 'Syllogisms', priority: 'medium', avgTime: '45s', successRate: '65%', difficulty: 'Medium', questions: 50 },
        { name: 'Puzzles & Seating Arrangement', priority: 'high', avgTime: '180s', successRate: '45%', difficulty: 'Hard', questions: 85 },
        { name: 'Coding-Decoding', priority: 'medium', avgTime: '50s', successRate: '80%', difficulty: 'Easy', questions: 55 },
        { name: 'Series & Pattern Recognition', priority: 'high', avgTime: '40s', successRate: '85%', difficulty: 'Easy', questions: 65 },
        { name: 'Data Sufficiency', priority: 'low', avgTime: '90s', successRate: '55%', difficulty: 'Hard', questions: 40 }
      ]
    },
    {
      id: 'verbal',
      title: 'Verbal Ability',
      icon: FileText,
      description: 'English language proficiency',
      color: 'bg-green-600',
      successRate: '82%',
      avgScore: '75%',
      trending: false,
      totalQuestions: 320,
      subtopics: [
        { name: 'Reading Comprehension', priority: 'high', avgTime: '300s', successRate: '70%', difficulty: 'Medium', questions: 80 },
        { name: 'Error Spotting', priority: 'medium', avgTime: '30s', successRate: '75%', difficulty: 'Easy', questions: 60 },
        { name: 'Sentence Improvement', priority: 'medium', avgTime: '35s', successRate: '80%', difficulty: 'Easy', questions: 55 },
        { name: 'Para Jumbles', priority: 'low', avgTime: '120s', successRate: '60%', difficulty: 'Medium', questions: 45 },
        { name: 'Fill in the Blanks', priority: 'high', avgTime: '25s', successRate: '85%', difficulty: 'Easy', questions: 50 },
        { name: 'Synonyms & Antonyms', priority: 'medium', avgTime: '20s', successRate: '90%', difficulty: 'Easy', questions: 30 }
      ]
    },
    {
      id: 'data-interpretation',
      title: 'Data Interpretation',
      icon: BarChart3,
      description: 'Analyzing charts, graphs, and data',
      color: 'bg-orange-600',
      successRate: '58%',
      avgScore: '62%',
      trending: true,
      totalQuestions: 280,
      subtopics: [
        { name: 'Pie Charts', priority: 'high', avgTime: '150s', successRate: '65%', difficulty: 'Medium', questions: 70 },
        { name: 'Bar Graphs', priority: 'high', avgTime: '120s', successRate: '70%', difficulty: 'Medium', questions: 65 },
        { name: 'Line Graphs', priority: 'medium', avgTime: '135s', successRate: '60%', difficulty: 'Medium', questions: 60 },
        { name: 'Tables', priority: 'medium', avgTime: '90s', successRate: '75%', difficulty: 'Easy', questions: 55 },
        { name: 'Caselets', priority: 'low', avgTime: '240s', successRate: '45%', difficulty: 'Hard', questions: 30 }
      ]
    }
  ];

  // Company-Specific Intelligence with detailed patterns
  const companyPatterns = {
    'TCS': {
      pattern: 'Focus on basic concepts, speed is key',
      topics: ['Percentages', 'Profit & Loss', 'Time & Work'],
      difficulty: 'Easy to Medium',
      passingScore: '60%',
      totalQuestions: 30,
      timeLimit: '90 minutes',
      tips: ['Negative marking: -1 for wrong answer', 'Calculators not allowed', 'Focus on speed over complexity'],
      recentTrends: 'Increased focus on logical puzzles',
      successRate: '45%',
      sectionBreakdown: {
        'Quantitative': 10,
        'Logical': 10,
        'Verbal': 10
      },
      cutoffTrends: 'Usually 18-20 out of 30',
      preparation: 'Practice daily for 2-3 hours, focus on accuracy'
    },
    'Infosys': {
      pattern: 'Heavy on Logical Reasoning and puzzles',
      topics: ['Puzzles', 'Blood Relations', 'Data Sufficiency'],
      difficulty: 'Medium to Hard',
      passingScore: '65%',
      totalQuestions: 40,
      timeLimit: '60 minutes',
      tips: ['No negative marking', 'Focus on accuracy over speed', 'Strong English section'],
      recentChanges: 'Added coding questions in 2024',
      successRate: '38%',
      sectionBreakdown: {
        'Quantitative': 10,
        'Logical': 15,
        'Verbal': 15
      },
      cutoffTrends: 'Sectional cutoffs: 4/6/6',
      preparation: 'Strong focus on English and reasoning'
    },
    'Wipro': {
      pattern: 'Balanced approach across all sections',
      topics: ['All sections equally weighted'],
      difficulty: 'Medium',
      passingScore: '55%',
      totalQuestions: 50,
      timeLimit: '75 minutes',
      tips: ['Sectional cutoffs apply', 'Good English is crucial', 'Time management important'],
      successRate: '42%',
      sectionBreakdown: {
        'Quantitative': 20,
        'Logical': 15,
        'Verbal': 15
      },
      cutoffTrends: 'Overall 28-30 out of 50',
      preparation: 'Equal emphasis on all sections'
    }
  };

  // Personalized Learning Paths
  const learningPaths = {
    'engineering': {
      name: 'Engineering Students',
      icon: Code,
      focus: ['Quantitative Aptitude', 'Logical Reasoning'],
      companies: ['TCS', 'Infosys', 'Wipro', 'Cognizant'],
      description: 'Optimized for tech placement preparation',
      duration: '8-12 weeks',
      weeklyPlan: {
        week1: 'Foundation building - Basic concepts',
        week2: 'Speed development - Time management',
        week3: 'Advanced problem solving',
        week4: 'Mock tests and analysis'
      }
    },
    'mba-prep': {
      name: 'MBA Aspirants',
      icon: GraduationCap,
      focus: ['Data Interpretation', 'Verbal Ability'],
      companies: ['Consulting firms', 'Finance companies'],
      description: 'CAT, XAT, SNAP preparation focused',
      duration: '12-16 weeks',
      weeklyPlan: {
        week1: 'Reading comprehension mastery',
        week2: 'Data analysis techniques',
        week3: 'Advanced verbal skills',
        week4: 'Mock CAT preparation'
      }
    },
    'government': {
      name: 'Government Exams',
      icon: Building2,
      focus: ['Quantitative Aptitude', 'Reasoning'],
      exams: ['SSC', 'Banking', 'Railway'],
      description: 'Public sector exam preparation',
      duration: '6-10 weeks',
      weeklyPlan: {
        week1: 'Arithmetic fundamentals',
        week2: 'Advanced reasoning',
        week3: 'Current affairs integration',
        week4: 'Exam strategy'
      }
    }
  };

  // Study Mode Options with detailed descriptions
  const studyModes = [
    {
      id: 'learn',
      name: 'Learn Mode',
      icon: BookMarked,
      description: 'Concepts + Examples + Practice',
      color: 'bg-blue-600',
      features: ['Step-by-step solutions', 'Concept videos', 'Practice exercises']
    },
    {
      id: 'speed',
      name: 'Speed Mode',
      icon: Zap,
      description: 'Timed questions for speed building',
      color: 'bg-yellow-600',
      features: ['Countdown timer', 'Speed tracking', 'Quick techniques']
    },
    {
      id: 'challenge',
      name: 'Challenge Mode',
      icon: Gamepad2,
      description: 'Difficult questions only',
      color: 'bg-red-600',
      features: ['Expert level questions', 'Competition prep', 'Advanced concepts']
    },
    {
      id: 'mock',
      name: 'Mock Test Mode',
      icon: Timer,
      description: 'Full-length simulation',
      color: 'bg-green-600',
      features: ['Real exam interface', 'Detailed analysis', 'Performance tracking']
    },
    {
      id: 'revision',
      name: 'Revision Mode',
      icon: RotateCcw,
      description: 'Previously incorrect questions',
      color: 'bg-purple-600',
      features: ['Wrong answer review', 'Concept clarification', 'Improvement tracking']
    },
    {
      id: 'target',
      name: 'Target Mode',
      icon: Target,
      description: 'Practice for specific company',
      color: 'bg-orange-600',
      features: ['Company patterns', 'Specific preparation', 'Success strategies']
    }
  ];

  // Enhanced companies with comprehensive data
  const companies = [
    { 
      name: 'TCS NQT', 
      logo: Building2, 
      difficulty: 'Easy-Medium',
      passRate: '45%',
      pattern: companyPatterns['TCS'],
      recentHiring: '50,000+ annually',
      avgPackage: '3.5 LPA'
    },
    { 
      name: 'Infosys', 
      logo: Building2,
      difficulty: 'Medium-Hard',
      passRate: '38%',
      pattern: companyPatterns['Infosys'],
      recentHiring: '35,000+ annually',
      avgPackage: '4.0 LPA'
    },
    { 
      name: 'Wipro Elite', 
      logo: Building2,
      difficulty: 'Medium',
      passRate: '42%',
      pattern: companyPatterns['Wipro'],
      recentHiring: '25,000+ annually',
      avgPackage: '3.8 LPA'
    },
    { name: 'Cognizant GenC', logo: Building2, difficulty: 'Medium', passRate: '40%', avgPackage: '4.2 LPA' },
    { name: 'Accenture', logo: Building2, difficulty: 'Easy-Medium', passRate: '50%', avgPackage: '4.5 LPA' },
    { name: 'Capgemini', logo: Building2, difficulty: 'Medium', passRate: '35%', avgPackage: '3.9 LPA' },
    { name: 'Tech Mahindra', logo: Building2, difficulty: 'Medium', passRate: '38%', avgPackage: '3.7 LPA' },
    { name: 'HCL', logo: Building2, difficulty: 'Easy-Medium', passRate: '48%', avgPackage: '3.6 LPA' }
  ];

  // Job categories for technical questions
  const jobCategories = [
    {
      title: 'Software & Engineering',
      icon: Code,
      jobs: [
        'Frontend Developer', 'Backend Engineer', 'Full Stack Developer',
        'Software Engineer', 'Mobile App Developer', 'Game Developer',
        'Embedded Systems Engineer', 'DevOps Engineer', 'Site Reliability Engineer (SRE)'
      ]
    },
    {
      title: 'Data & AI',
      icon: BookOpen,
      jobs: [
        'Data Scientist', 'Data Analyst', 'Machine Learning Engineer',
        'Data Engineer', 'AI Researcher', 'Business Intelligence (BI) Analyst',
        'Statistician'
      ]
    },
    {
      title: 'Cloud & Infrastructure',
      icon: Search,
      jobs: [
        'Cloud Engineer', 'Solutions Architect', 'Security Engineer',
        'Network Engineer', 'Cloud DevOps Engineer'
      ]
    },
    {
      title: 'Design & UX',
      icon: Users,
      jobs: [
        'UX Designer', 'UI Designer', 'Product Designer',
        'UX Researcher', 'Interaction Designer'
      ]
    },
    {
      title: 'Quality & Testing',
      icon: Search,
      jobs: [
        'QA Tester', 'Automation Test Engineer', 'Performance Tester',
        'Security Tester', 'Manual Tester'
      ]
    },
    {
      title: 'Product & Management',
      icon: Users,
      jobs: [
        'Product Manager', 'Technical Product Manager', 'Project Manager',
        'Scrum Master', 'Program Manager'
      ]
    }
  ];

  const filteredJobs = jobCategories.map(category => ({
    ...category,
    jobs: category.jobs.filter(job => 
      job.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.jobs.length > 0);

  const handleJobSelect = (job) => {
    setSelectedJobTitle(job);
    setSearchQuery(job);
  };

  const handleButtonClick = (type) => {
    if (type === 'technical') {
      setIsTechnicalModalOpen(true);
    } else if (type === 'aptitude') {
      setIsAptitudeModalOpen(true);
    } else {
      toast({
        title: "Coming Soon!",
        description: `${type} questions will be available soon.`
      });
    }
  };

  const handleAptitudeCategorySelect = (category) => {
    setSelectedAptitudeCategory(category.id);
  };

  const handleSubtopicSelect = (subtopic) => {
    setSelectedSubtopic(subtopic);
  };

  const handleDifficultySelect = (difficulty) => {
    setSelectedDifficulty(difficulty.id);
  };

  const handleLearningPathSelect = (path) => {
    setSelectedLearningPath(path.name);
  };

  const handleStudyModeSelect = (mode) => {
    setSelectedStudyMode(mode.id);
  };

  const handleCompanySelect = (company) => {
    setSelectedCompany(company.name);
  };

  const handleStartPractice = () => {
    if (!selectedAptitudeCategory || !selectedDifficulty) {
      toast({
        title: "Selection Required",
        description: "Please select a category and difficulty level to start practice."
      });
      return;
    }
    
    const category = aptitudeCategories.find(cat => cat.id === selectedAptitudeCategory);
    const difficulty = smartLevels.find(level => level.id === selectedDifficulty);
    
    toast({
      title: "🚀 Starting Enhanced Practice Session!",
      description: `Loading ${difficulty?.name} level ${category?.title} with AI-powered insights...`
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Enhanced Header with Stats */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-yellow-400" />
            <h1 className="text-4xl font-bold text-white">Interview Questions</h1>
            <Badge className="bg-gradient-to-r from-red-500 to-orange-500 text-white animate-pulse">
              <Sparkles className="w-3 h-3 mr-1" />
              WORLD-CLASS
            </Badge>
          </div>
          <div className="text-right text-white/80 text-sm">
            <div>📊 1,430+ Questions</div>
            <div>🎯 78% Success Rate</div>
          </div>
        </div>

        {/* Job Title Input */}
        <div className="mb-8">
          <label className="block text-white text-lg font-medium mb-4 text-center">
            Job Title
          </label>
          <div className="relative max-w-2xl mx-auto">
            <Input
              type="text"
              placeholder="e.g. Frontend Developer, Data Scientist, Backend Engineer"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full py-4 px-6 text-lg bg-white/10 border-white/20 text-white placeholder:text-white/60 backdrop-blur-sm rounded-xl"
            />
          </div>
          <p className="text-center text-white/80 mt-3">
            Enter a job title to generate relevant interview questions
          </p>
        </div>

        {/* Enhanced Question Type Buttons */}
        <div className="space-y-4 mb-12 max-w-2xl mx-auto">
          <Button
            onClick={() => handleButtonClick('aptitude')}
            className="w-full py-6 px-8 text-left bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105"
          >
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-2 rounded-lg">
                <BookOpen className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-semibold">Aptitude Questions</h3>
                  <Badge className="bg-red-500 text-white text-xs animate-bounce">
                    <Flame className="w-3 h-3 mr-1" />
                    ENHANCED
                  </Badge>
                </div>
                <p className="text-blue-100 text-sm">Numerical, Logical, Verbal & Spatial Reasoning</p>
                <div className="flex gap-4 mt-2 text-xs text-blue-200">
                  <span>📚 1,430+ Questions</span>
                  <span>🏢 8+ Companies</span>
                  <span>🎯 Smart Analytics</span>
                </div>
              </div>
            </div>
          </Button>

          <Button
            onClick={() => handleButtonClick('technical')}
            className="w-full py-6 px-8 text-left bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105"
          >
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-2 rounded-lg">
                <Code className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Technical Interview Questions</h3>
                <p className="text-orange-100 text-sm">Role-specific technical challenges and problem-solving</p>
              </div>
            </div>
          </Button>

          <Button
            onClick={() => handleButtonClick('behavioral')}
            className="w-full py-6 px-8 text-left bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-700 hover:to-teal-800 text-white rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105"
          >
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-2 rounded-lg">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-semibold">Behavioral Interview Questions</h3>
                <p className="text-teal-100 text-sm">Soft skills, teamwork, and situational responses</p>
              </div>
            </div>
          </Button>
        </div>

        {/* Quick Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white/10 border-white/20 text-center">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-400">85%</div>
              <div className="text-sm text-blue-200">Success Rate</div>
            </CardContent>
          </Card>
          <Card className="bg-white/10 border-white/20 text-center">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-yellow-400">1,430+</div>
              <div className="text-sm text-blue-200">Questions</div>
            </CardContent>
          </Card>
          <Card className="bg-white/10 border-white/20 text-center">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-400">50K+</div>
              <div className="text-sm text-blue-200">Students</div>
            </CardContent>
          </Card>
          <Card className="bg-white/10 border-white/20 text-center">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-purple-400">Top 5%</div>
              <div className="text-sm text-blue-200">Ranking</div>
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Quick Tips Section */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
          <div className="flex items-center gap-3 mb-4">
            <Lightbulb className="w-6 h-6 text-yellow-400" />
            <h3 className="text-xl font-semibold text-white">💡 Pro Tips for Better Results:</h3>
          </div>
          <ul className="space-y-3 text-white/90">
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">🎯</span>
              <span>Be specific with job titles (e.g., "React Developer" vs "Developer")</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">📈</span>
              <span>Include seniority level (Junior, Senior, Lead, Principal)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">🏥</span>
              <span>Add domain context (e.g., "Healthcare Data Analyst", "E-commerce Backend Developer")</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">⚡</span>
              <span>Specify technologies if relevant (e.g., "Python ML Engineer", "React Native Developer")</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Comprehensive Aptitude Questions Modal */}
      <Dialog open={isAptitudeModalOpen} onOpenChange={setIsAptitudeModalOpen}>
        <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto bg-gradient-to-br from-indigo-900 via-blue-900 to-cyan-900 border-blue-700/50 text-white [&>button]:hidden">
          <DialogHeader className="pb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Target className="w-7 h-7 text-cyan-400" />
                <DialogTitle className="text-3xl font-bold text-white">
                  🎯 Aptitude Questions – Placement Preparation
                </DialogTitle>
                <Badge className="bg-gradient-to-r from-red-500 to-orange-500 text-white animate-pulse">
                  <Flame className="w-3 h-3 mr-1" />
                  WORLD-CLASS
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsAptitudeModalOpen(false)}
                className="text-white hover:bg-white/10"
              >
                <X className="w-6 h-6" />
              </Button>
            </div>
            <p className="text-blue-200 text-lg mt-2">
              🚀 Choose an Aptitude Category for Your Tech Placement Preparation
            </p>
          </DialogHeader>

          <Tabs defaultValue="categories" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 bg-white/10 border border-white/20">
              <TabsTrigger value="categories" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                📚 Practice by Category
              </TabsTrigger>
              <TabsTrigger value="companies" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                🏢 Company-Specific
              </TabsTrigger>
              <TabsTrigger value="analytics" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                📊 Performance Analytics
              </TabsTrigger>
              <TabsTrigger value="paths" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                🛤️ Learning Paths
              </TabsTrigger>
            </TabsList>

            {/* Categories Tab with all enhancements */}
            <TabsContent value="categories" className="space-y-6">
              {/* Trending Topics Banner */}
              <div className="bg-gradient-to-r from-red-600/20 to-orange-600/20 rounded-xl p-4 border border-red-500/50">
                <div className="flex items-center gap-3 mb-3">
                  <TrendingUp className="w-5 h-5 text-red-400" />
                  <h3 className="text-lg font-semibold text-white">🔥 Trending This Week</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className="bg-red-500 text-white">
                    <Flame className="w-3 h-3 mr-1" />
                    Puzzles & Seating Arrangement
                  </Badge>
                  <Badge className="bg-orange-500 text-white">
                    <Star className="w-3 h-3 mr-1" />
                    Data Interpretation
                  </Badge>
                  <Badge className="bg-yellow-500 text-black">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Time & Work
                  </Badge>
                </div>
              </div>

              {/* Enhanced Main Categories */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {aptitudeCategories.map((category) => (
                  <Card 
                    key={category.id} 
                    className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                      selectedAptitudeCategory === category.id 
                        ? 'border-cyan-400 bg-white/20' 
                        : 'border-white/20 bg-white/10'
                    } hover:bg-white/20 relative overflow-hidden`}
                    onClick={() => handleAptitudeCategorySelect(category)}
                  >
                    {category.trending && (
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-red-500 text-white text-xs animate-pulse">
                          <Flame className="w-3 h-3 mr-1" />
                          HOT
                        </Badge>
                      </div>
                    )}
                    
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-lg ${category.color}`}>
                          <category.icon className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1">
                          <CardTitle className="text-white text-xl flex items-center gap-2">
                            {category.title}
                            {category.trending && <TrendingUp className="w-4 h-4 text-red-400" />}
                          </CardTitle>
                          <CardDescription className="text-blue-200 mt-1">
                            {category.description}
                          </CardDescription>
                          
                          {/* Enhanced Stats */}
                          <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                            <span className="text-green-300">
                              📈 {category.successRate}
                            </span>
                            <span className="text-blue-300">
                              📊 {category.avgScore}
                            </span>
                            <span className="text-yellow-300">
                              📝 {category.totalQuestions}Q
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2 mb-3">
                        {category.subtopics.slice(0, 4).map((subtopic, index) => {
                          const priority = getTopicPriority(subtopic.name);
                          return (
                            <div key={index} className="relative">
                              <Badge 
                                variant="secondary" 
                                className="bg-white/20 text-white text-xs px-2 py-1"
                              >
                                {subtopic.name}
                              </Badge>
                              <div className={`absolute -top-1 -right-1 w-2 h-2 rounded-full ${priority.color}`}></div>
                            </div>
                          );
                        })}
                        {category.subtopics.length > 4 && (
                          <Badge variant="secondary" className="bg-white/20 text-white text-xs px-2 py-1">
                            +{category.subtopics.length - 4} more
                          </Badge>
                        )}
                      </div>
                      
                      {/* Progress Visualization */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-blue-200">
                          <span>Your Progress</span>
                          <span>65%</span>
                        </div>
                        <Progress value={65} className="h-2 bg-white/20" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Enhanced Subtopics Selection */}
              {selectedAptitudeCategory && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-cyan-400" />
                    Choose Specific Topics with Smart Insights
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {aptitudeCategories
                      .find(cat => cat.id === selectedAptitudeCategory)
                      ?.subtopics.map((subtopic, index) => {
                        const priority = getTopicPriority(subtopic.name);
                        const timeInfo = timeManagementTips[subtopic.name];
                        
                        return (
                          <Card
                            key={index}
                            className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                              selectedSubtopic === subtopic.name
                                ? 'border-cyan-400 bg-white/20'
                                : 'border-white/20 bg-white/10'
                            } hover:bg-white/20`}
                            onClick={() => handleSubtopicSelect(subtopic.name)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold text-white text-sm">{subtopic.name}</h4>
                                <Badge className={`${priority.color} text-white text-xs`}>
                                  {priority.badge}
                                </Badge>
                              </div>
                              
                              <div className="space-y-2 text-xs text-blue-200">
                                <div className="flex justify-between">
                                  <span>⏱️ Avg Time:</span>
                                  <span className="text-yellow-300">{subtopic.avgTime}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>📈 Success Rate:</span>
                                  <span className="text-green-300">{subtopic.successRate}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>📝 Questions:</span>
                                  <span className="text-blue-300">{subtopic.questions}</span>
                                </div>
                                {timeInfo && (
                                  <div className="mt-2 p-2 bg-white/10 rounded text-xs">
                                    💡 {timeInfo.tip}
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* Smart Difficulty Level Selection */}
              {selectedAptitudeCategory && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Trophy className="w-5 h-5 text-cyan-400" />
                    Smart Difficulty Progression
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {smartLevels.map((level) => (
                      <Card
                        key={level.id}
                        className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                          selectedDifficulty === level.id
                            ? 'border-cyan-400 bg-white/20'
                            : 'border-white/20 bg-white/10'
                        } hover:bg-white/20`}
                        onClick={() => handleDifficultySelect(level)}
                      >
                        <CardContent className="p-4 text-center">
                          <div className={`w-12 h-12 mx-auto mb-3 rounded-full ${level.color} flex items-center justify-center`}>
                            <level.icon className="w-6 h-6 text-white" />
                          </div>
                          <h4 className="text-white font-semibold text-lg">{level.name}</h4>
                          <p className="text-blue-200 text-sm mt-1">{level.description}</p>
                          <div className="mt-3 space-y-1 text-xs text-blue-300">
                            <div>📝 {level.questionCount}</div>
                            <div>⏰ {level.timeLimit}</div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Study Modes Selection */}
              {selectedAptitudeCategory && selectedDifficulty && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Gamepad2 className="w-5 h-5 text-cyan-400" />
                    Choose Your Study Mode
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {studyModes.map((mode) => (
                      <Card
                        key={mode.id}
                        className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                          selectedStudyMode === mode.id
                            ? 'border-cyan-400 bg-white/20'
                            : 'border-white/20 bg-white/10'
                        } hover:bg-white/20`}
                        onClick={() => handleStudyModeSelect(mode)}
                      >
                        <CardContent className="p-4 text-center">
                          <div className={`w-10 h-10 mx-auto mb-2 rounded-full ${mode.color} flex items-center justify-center`}>
                            <mode.icon className="w-5 h-5 text-white" />
                          </div>
                          <h4 className="text-white font-semibold text-sm">{mode.name}</h4>
                          <p className="text-blue-200 text-xs mt-1">{mode.description}</p>
                          <div className="mt-2 text-xs text-blue-300">
                            {mode.features?.map((feature, idx) => (
                              <div key={idx}>• {feature}</div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {selectedAptitudeCategory && selectedDifficulty && (
                <div className="flex justify-center pt-6">
                  <Button 
                    onClick={handleStartPractice}
                    className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white px-12 py-4 text-xl font-bold rounded-xl shadow-xl transition-all duration-300 hover:shadow-2xl hover:scale-110"
                  >
                    <PlayCircle className="w-8 h-8 mr-4" />
                    🚀 Start World-Class Practice Session
                    <Sparkles className="w-6 h-6 ml-4" />
                  </Button>
                </div>
              )}
            </TabsContent>

            {/* Company-Specific Tab */}
            <TabsContent value="companies" className="space-y-6">
              <div className="text-center space-y-4">
                <h3 className="text-2xl font-semibold text-white">
                  🏢 Company-Specific Placement Practice
                </h3>
                <p className="text-blue-200">Practice with real placement exam patterns and difficulty levels</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {companies.map((company, index) => (
                  <Card
                    key={index}
                    className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                      selectedCompany === company.name
                        ? 'border-cyan-400 bg-white/20'
                        : 'border-white/20 bg-white/10'
                    } hover:bg-white/20 hover:border-cyan-400`}
                    onClick={() => handleCompanySelect(company)}
                  >
                    <CardContent className="p-4 text-center">
                      <company.logo className="w-8 h-8 mx-auto mb-3 text-cyan-400" />
                      <h4 className="text-white font-semibold mb-2">{company.name}</h4>
                      <div className="space-y-1 text-xs text-blue-200">
                        <div className="flex justify-between">
                          <span>Difficulty:</span>
                          <span className="text-yellow-300">{company.difficulty}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Pass Rate:</span>
                          <span className="text-green-300">{company.passRate}</span>
                        </div>
                        {company.avgPackage && (
                          <div className="flex justify-between">
                            <span>Avg Package:</span>
                            <span className="text-purple-300">{company.avgPackage}</span>
                          </div>
                        )}
                      </div>
                      {company.pattern && (
                        <div className="mt-2 p-2 bg-white/10 rounded text-xs">
                          💡 {company.pattern.pattern}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Detailed Company Analysis */}
              {selectedCompany && (
                <Card className="bg-white/10 border-white/20">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-cyan-400" />
                      {selectedCompany} - Detailed Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {Object.entries(companyPatterns).map(([companyKey, pattern]) => {
                      if (selectedCompany.includes(companyKey)) {
                        return (
                          <div key={companyKey} className="space-y-3">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-200">
                              <div>
                                <span className="font-semibold text-white">Pattern:</span>
                                <p>{pattern.pattern}</p>
                              </div>
                              <div>
                                <span className="font-semibold text-white">Difficulty:</span>
                                <p>{pattern.difficulty}</p>
                              </div>
                              <div>
                                <span className="font-semibold text-white">Total Questions:</span>
                                <p>{pattern.totalQuestions} questions</p>
                              </div>
                              <div>
                                <span className="font-semibold text-white">Time Limit:</span>
                                <p>{pattern.timeLimit}</p>
                              </div>
                            </div>
                            
                            <div>
                              <span className="font-semibold text-white">Key Tips:</span>
                              <ul className="list-disc list-inside mt-2 text-blue-200 text-sm">
                                {pattern.tips.map((tip, idx) => (
                                  <li key={idx}>{tip}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })}
                  </CardContent>
                </Card>
              )}
              
              {/* Enhanced Mock Test Options */}
              <div className="bg-white/10 rounded-xl p-6 border border-white/20">
                <h4 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-cyan-400" />
                  Advanced Practice Modes
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Target className="w-6 h-6 text-cyan-400" />
                    <span>Topic-wise Practice</span>
                    <span className="text-xs text-blue-300">Focus on weak areas</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Timer className="w-6 h-6 text-green-400" />
                    <span>Full Mock Tests</span>
                    <span className="text-xs text-blue-300">Real exam simulation</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-yellow-400" />
                    <span>Progress Analytics</span>
                    <span className="text-xs text-blue-300">Detailed insights</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Trophy className="w-6 h-6 text-purple-400" />
                    <span>Daily Challenges</span>
                    <span className="text-xs text-blue-300">Compete with peers</span>
                  </Button>
                </div>
              </div>
            </TabsContent>

            {/* Performance Analytics Tab */}
            <TabsContent value="analytics" className="space-y-6">
              <div className="text-center space-y-4">
                <h3 className="text-2xl font-semibold text-white flex items-center justify-center gap-2">
                  <BarChart3 className="w-6 h-6 text-cyan-400" />
                  📊 Your Performance Analytics Dashboard
                </h3>
                <p className="text-blue-200">Track your progress and identify areas for improvement</p>
              </div>

              {/* Performance Overview */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-green-400">85%</div>
                    <div className="text-sm text-blue-200">Overall Accuracy</div>
                    <Progress value={85} className="mt-2 h-2" />
                  </CardContent>
                </Card>
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-yellow-400">127</div>
                    <div className="text-sm text-blue-200">Questions Solved</div>
                    <div className="text-xs text-green-300 mt-1">↑ 23 this week</div>
                  </CardContent>
                </Card>
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-blue-400">18</div>
                    <div className="text-sm text-blue-200">Study Streak</div>
                    <div className="text-xs text-green-300 mt-1">🔥 Keep it up!</div>
                  </CardContent>
                </Card>
                <Card className="bg-white/10 border-white/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-purple-400">Top 15%</div>
                    <div className="text-sm text-blue-200">Class Ranking</div>
                    <div className="text-xs text-green-300 mt-1">↑ 5 positions</div>
                  </CardContent>
                </Card>
              </div>

              {/* Weak Areas Analysis */}
              <Card className="bg-white/10 border-white/20">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Target className="w-5 h-5 text-red-400" />
                    🎯 Areas Needing Attention
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white">Permutations & Combinations</span>
                      <span className="text-red-400">45% accuracy</span>
                    </div>
                    <Progress value={45} className="h-2" />
                    <p className="text-xs text-blue-300">💡 Suggested: Practice 15 more questions</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white">Data Interpretation</span>
                      <span className="text-yellow-400">62% accuracy</span>
                    </div>
                    <Progress value={62} className="h-2" />
                    <p className="text-xs text-blue-300">💡 Focus on: Chart reading speed</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-white">Puzzles & Seating Arrangement</span>
                      <span className="text-orange-400">58% accuracy</span>
                    </div>
                    <Progress value={58} className="h-2" />
                    <p className="text-xs text-blue-300">💡 Practice: Complex arrangement patterns</p>
                  </div>
                </CardContent>
              </Card>

              {/* Study Recommendations */}
              <Card className="bg-white/10 border-white/20">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                    🎓 Personalized Study Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <Clock className="w-5 h-5 text-blue-400" />
                    <div>
                      <div className="text-white font-medium">Today's Goal</div>
                      <div className="text-blue-200 text-sm">Complete 20 Percentage questions</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <Calendar className="w-5 h-5 text-green-400" />
                    <div>
                      <div className="text-white font-medium">This Week</div>
                      <div className="text-blue-200 text-sm">Focus on Time & Work problems</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <Trophy className="w-5 h-5 text-purple-400" />
                    <div>
                      <div className="text-white font-medium">Monthly Target</div>
                      <div className="text-blue-200 text-sm">Achieve 90% in Quantitative Aptitude</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Performance Charts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="bg-white/10 border-white/20">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <LineChart className="w-5 h-5 text-cyan-400" />
                      Weekly Progress
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-32 flex items-end justify-between gap-2">
                      {[65, 72, 68, 75, 82, 78, 85].map((value, index) => (
                        <div key={index} className="flex flex-col items-center">
                          <div 
                            className="bg-cyan-500 w-6 rounded-t"
                            style={{ height: `${value}%` }}
                          ></div>
                          <span className="text-xs text-blue-300 mt-1">Day {index + 1}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-white/10 border-white/20">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <PieChart className="w-5 h-5 text-cyan-400" />
                      Category Performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-blue-200">Quantitative</span>
                      <div className="flex items-center gap-2">
                        <Progress value={78} className="w-20 h-2" />
                        <span className="text-green-400 text-sm">78%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-blue-200">Logical</span>
                      <div className="flex items-center gap-2">
                        <Progress value={65} className="w-20 h-2" />
                        <span className="text-yellow-400 text-sm">65%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-blue-200">Verbal</span>
                      <div className="flex items-center gap-2">
                        <Progress value={82} className="w-20 h-2" />
                        <span className="text-green-400 text-sm">82%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-blue-200">Data Interpretation</span>
                      <div className="flex items-center gap-2">
                        <Progress value={58} className="w-20 h-2" />
                        <span className="text-red-400 text-sm">58%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Learning Paths Tab */}
            <TabsContent value="paths" className="space-y-6">
              <div className="text-center space-y-4">
                <h3 className="text-2xl font-semibold text-white flex items-center justify-center gap-2">
                  <GraduationCap className="w-6 h-6 text-cyan-400" />
                  🛤️ Personalized Learning Paths
                </h3>
                <p className="text-blue-200">Choose a path tailored to your career goals</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.values(learningPaths).map((path, index) => (
                  <Card
                    key={index}
                    className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                      selectedLearningPath === path.name
                        ? 'border-cyan-400 bg-white/20'
                        : 'border-white/20 bg-white/10'
                    } hover:bg-white/20`}
                    onClick={() => handleLearningPathSelect(path)}
                  >
                    <CardHeader>
                      <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-cyan-600">
                          <path.icon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <CardTitle className="text-white">{path.name}</CardTitle>
                          <CardDescription className="text-blue-200">
                            {path.description}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <div className="text-white font-medium text-sm mb-2">📚 Focus Areas:</div>
                        <div className="flex flex-wrap gap-1">
                          {path.focus.map((area, idx) => (
                            <Badge key={idx} variant="secondary" className="bg-white/20 text-white text-xs">
                              {area}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-white font-medium text-sm mb-2">🏢 Target Companies:</div>
                        <div className="text-blue-200 text-xs">
                          {path.companies ? path.companies.join(', ') : path.exams?.join(', ')}
                        </div>
                      </div>
                      
                      <div className="flex justify-between text-xs text-blue-300">
                        <span>⏰ Duration: {path.duration}</span>
                        <span>🎯 Success Rate: 78%</span>
                      </div>

                      {path.weeklyPlan && (
                        <div>
                          <div className="text-white font-medium text-sm mb-2">📅 Weekly Plan:</div>
                          <div className="space-y-1 text-xs text-blue-200">
                            {Object.entries(path.weeklyPlan).map(([week, plan]) => (
                              <div key={week} className="flex gap-2">
                                <span className="text-cyan-400">{week}:</span>
                                <span>{plan}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Community Features */}
              <Card className="bg-white/10 border-white/20">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Users2 className="w-5 h-5 text-cyan-400" />
                    👥 Community Features
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <MessageCircle className="w-5 h-5 text-blue-400" />
                    <div>
                      <div className="text-white font-medium text-sm">Discussion Forums</div>
                      <div className="text-blue-200 text-xs">Get doubts cleared instantly</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <Trophy className="w-5 h-5 text-yellow-400" />
                    <div>
                      <div className="text-white font-medium text-sm">Success Stories</div>
                      <div className="text-blue-200 text-xs">Learn from toppers</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg">
                    <Users2 className="w-5 h-5 text-green-400" />
                    <div>
                      <div className="text-white font-medium text-sm">Peer Comparison</div>
                      <div className="text-blue-200 text-xs">See your college ranking</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Additional Learning Resources */}
              <Card className="bg-white/10 border-white/20">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-cyan-400" />
                    📚 Additional Learning Resources
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <PlayCircle className="w-6 h-6 text-blue-400" />
                    <span>Video Tutorials</span>
                    <span className="text-xs text-blue-300">Step-by-step guides</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Download className="w-6 h-6 text-green-400" />
                    <span>PDF Materials</span>
                    <span className="text-xs text-blue-300">Offline study guides</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Share2 className="w-6 h-6 text-yellow-400" />
                    <span>Share Progress</span>
                    <span className="text-xs text-blue-300">Social learning</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Bell className="w-6 h-6 text-purple-400" />
                    <span>Study Reminders</span>
                    <span className="text-xs text-blue-300">Stay consistent</span>
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Technical Interview Questions Modal - Unchanged */}
      <Dialog open={isTechnicalModalOpen} onOpenChange={setIsTechnicalModalOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-amber-900 via-orange-900 to-red-900 border-amber-700/50 text-white [&>button]:hidden">
          {/* Technical modal content remains the same... */}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ComprehensiveAptitudeQuestions;