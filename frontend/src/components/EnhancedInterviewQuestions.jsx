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
  PieChart, LineChart, Calendar, Bell, Sparkles
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const EnhancedInterviewQuestions = () => {
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
    }
  };

  // Topic Priority System
  const getTopicPriority = (topic) => {
    const highPriority = ['Percentages', 'Profit & Loss', 'Blood Relations', 'Puzzles & Seating Arrangement'];
    const mediumPriority = ['Time & Work', 'Averages', 'Direction Sense', 'Reading Comprehension'];
    
    if (highPriority.includes(topic)) {
      return { badge: 'HOT', color: 'bg-red-500', frequency: '90% of placement tests' };
    } else if (mediumPriority.includes(topic)) {
      return { badge: 'IMPORTANT', color: 'bg-orange-500', frequency: '60% of placement tests' };
    } else {
      return { badge: 'BONUS', color: 'bg-blue-500', frequency: '30% of placement tests' };
    }
  };

  // Enhanced Aptitude Categories with all improvements
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
      subtopics: [
        { name: 'Percentages', priority: 'high', avgTime: '45s', successRate: '85%' },
        { name: 'Profit & Loss', priority: 'high', avgTime: '60s', successRate: '72%' },
        { name: 'Time, Speed & Distance', priority: 'medium', avgTime: '90s', successRate: '65%' },
        { name: 'Time & Work', priority: 'medium', avgTime: '75s', successRate: '68%' },
        { name: 'Averages', priority: 'medium', avgTime: '50s', successRate: '80%' },
        { name: 'Number Systems', priority: 'low', avgTime: '40s', successRate: '75%' },
        { name: 'Simplification', priority: 'high', avgTime: '30s', successRate: '90%' },
        { name: 'HCF & LCM', priority: 'medium', avgTime: '55s', successRate: '70%' },
        { name: 'Permutations & Combinations', priority: 'low', avgTime: '120s', successRate: '45%' },
        { name: 'Probability', priority: 'low', avgTime: '100s', successRate: '50%' }
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
      subtopics: [
        { name: 'Blood Relations', priority: 'high', avgTime: '90s', successRate: '70%' },
        { name: 'Direction Sense', priority: 'medium', avgTime: '60s', successRate: '75%' },
        { name: 'Syllogisms', priority: 'medium', avgTime: '45s', successRate: '65%' },
        { name: 'Puzzles & Seating Arrangement', priority: 'high', avgTime: '180s', successRate: '45%' },
        { name: 'Coding-Decoding', priority: 'medium', avgTime: '50s', successRate: '80%' },
        { name: 'Series & Pattern Recognition', priority: 'high', avgTime: '40s', successRate: '85%' },
        { name: 'Data Sufficiency', priority: 'low', avgTime: '90s', successRate: '55%' }
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
      subtopics: [
        { name: 'Reading Comprehension', priority: 'high', avgTime: '300s', successRate: '70%' },
        { name: 'Error Spotting', priority: 'medium', avgTime: '30s', successRate: '75%' },
        { name: 'Sentence Improvement', priority: 'medium', avgTime: '35s', successRate: '80%' },
        { name: 'Para Jumbles', priority: 'low', avgTime: '120s', successRate: '60%' },
        { name: 'Fill in the Blanks', priority: 'high', avgTime: '25s', successRate: '85%' },
        { name: 'Synonyms & Antonyms', priority: 'medium', avgTime: '20s', successRate: '90%' }
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
      subtopics: [
        { name: 'Pie Charts', priority: 'high', avgTime: '150s', successRate: '65%' },
        { name: 'Bar Graphs', priority: 'high', avgTime: '120s', successRate: '70%' },
        { name: 'Line Graphs', priority: 'medium', avgTime: '135s', successRate: '60%' },
        { name: 'Tables', priority: 'medium', avgTime: '90s', successRate: '75%' },
        { name: 'Caselets', priority: 'low', avgTime: '240s', successRate: '45%' }
      ]
    }
  ];

  // Company-Specific Intelligence
  const companyPatterns = {
    'TCS': {
      pattern: 'Focus on basic concepts, speed is key',
      topics: ['Percentages', 'Profit & Loss', 'Time & Work'],
      difficulty: 'Easy to Medium',
      passingScore: '60%',
      totalQuestions: 30,
      timeLimit: '90 minutes',
      tips: ['Negative marking: -1 for wrong answer', 'Calculators not allowed'],
      recentTrends: 'Increased focus on logical puzzles',
      successRate: '45%'
    },
    'Infosys': {
      pattern: 'Heavy on Logical Reasoning and puzzles',
      topics: ['Puzzles', 'Blood Relations', 'Data Sufficiency'],
      difficulty: 'Medium to Hard',
      passingScore: '65%',
      totalQuestions: 40,
      timeLimit: '60 minutes',
      tips: ['No negative marking', 'Focus on accuracy over speed'],
      recentChanges: 'Added coding questions in 2024',
      successRate: '38%'
    },
    'Wipro': {
      pattern: 'Balanced approach across all sections',
      topics: ['All sections equally weighted'],
      difficulty: 'Medium',
      passingScore: '55%',
      totalQuestions: 50,
      timeLimit: '75 minutes',
      tips: ['Sectional cutoffs apply', 'Good English is crucial'],
      successRate: '42%'
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
      duration: '8-12 weeks'
    },
    'mba-prep': {
      name: 'MBA Aspirants',
      icon: GraduationCap,
      focus: ['Data Interpretation', 'Verbal Ability'],
      companies: ['Consulting firms', 'Finance companies'],
      description: 'CAT, XAT, SNAP preparation focused',
      duration: '12-16 weeks'
    },
    'government': {
      name: 'Government Exams',
      icon: Building2,
      focus: ['Quantitative Aptitude', 'Reasoning'],
      exams: ['SSC', 'Banking', 'Railway'],
      description: 'Public sector exam preparation',
      duration: '6-10 weeks'
    }
  };

  // Study Mode Options
  const studyModes = [
    {
      id: 'learn',
      name: 'Learn Mode',
      icon: BookMarked,
      description: 'Concepts + Examples + Practice',
      color: 'bg-blue-600'
    },
    {
      id: 'speed',
      name: 'Speed Mode',
      icon: Zap,
      description: 'Timed questions for speed building',
      color: 'bg-yellow-600'
    },
    {
      id: 'challenge',
      name: 'Challenge Mode',
      icon: Gamepad2,
      description: 'Difficult questions only',
      color: 'bg-red-600'
    },
    {
      id: 'mock',
      name: 'Mock Test Mode',
      icon: Timer,
      description: 'Full-length simulation',
      color: 'bg-green-600'
    },
    {
      id: 'revision',
      name: 'Revision Mode',
      icon: RotateCcw,
      description: 'Previously incorrect questions',
      color: 'bg-purple-600'
    },
    {
      id: 'target',
      name: 'Target Mode',
      icon: Target,
      description: 'Practice for specific company',
      color: 'bg-orange-600'
    }
  ];

  // Enhanced companies with detailed info
  const companies = [
    { 
      name: 'TCS NQT', 
      logo: Building2, 
      difficulty: 'Easy-Medium',
      passRate: '45%',
      pattern: companyPatterns['TCS']
    },
    { 
      name: 'Infosys', 
      logo: Building2,
      difficulty: 'Medium-Hard',
      passRate: '38%',
      pattern: companyPatterns['Infosys']
    },
    { 
      name: 'Wipro Elite', 
      logo: Building2,
      difficulty: 'Medium',
      passRate: '42%',
      pattern: companyPatterns['Wipro']
    },
    { name: 'Cognizant GenC', logo: Building2, difficulty: 'Medium', passRate: '40%' },
    { name: 'Accenture', logo: Building2, difficulty: 'Easy-Medium', passRate: '50%' },
    { name: 'Capgemini', logo: Building2, difficulty: 'Medium', passRate: '35%' },
    { name: 'Tech Mahindra', logo: Building2, difficulty: 'Medium', passRate: '38%' },
    { name: 'HCL', logo: Building2, difficulty: 'Easy-Medium', passRate: '48%' }
  ];

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

  const handleStartPractice = () => {
    if (!selectedAptitudeCategory || !selectedDifficulty) {
      toast({
        title: "Selection Required",
        description: "Please select a category and difficulty level to start practice."
      });
      return;
    }
    toast({
      title: "Starting Practice Session! 🚀",
      description: `Loading ${selectedDifficulty} level questions for ${selectedAptitudeCategory}...`
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <BookOpen className="w-8 h-8 text-yellow-400" />
          <h1 className="text-4xl font-bold text-white">Interview Questions</h1>
          <Badge className="bg-yellow-500 text-black animate-pulse">
            <Sparkles className="w-3 h-3 mr-1" />
            Enhanced
          </Badge>
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

        {/* Question Type Buttons */}
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

        {/* Quick Tips Section */}
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
          <div className="flex items-center gap-3 mb-4">
            <Lightbulb className="w-6 h-6 text-yellow-400" />
            <h3 className="text-xl font-semibold text-white">Quick Tips for Better Results:</h3>
          </div>
          <ul className="space-y-3 text-white/90">
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">•</span>
              <span>Be specific with job titles (e.g., "React Developer" vs "Developer")</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">•</span>
              <span>Include seniority level (Junior, Senior, Lead, Principal)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">•</span>
              <span>Add domain context (e.g., "Healthcare Data Analyst", "E-commerce Backend Developer")</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-1">•</span>
              <span>Specify technologies if relevant (e.g., "Python ML Engineer", "React Native Developer")</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Technical Interview Questions Modal */}
      <Dialog open={isTechnicalModalOpen} onOpenChange={setIsTechnicalModalOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-amber-900 via-orange-900 to-red-900 border-amber-700/50 text-white [&>button]:hidden">
          <DialogHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Code className="w-6 h-6 text-white" />
                <DialogTitle className="text-2xl font-bold text-white">Select a Job Title</DialogTitle>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsTechnicalModalOpen(false)}
                className="text-white hover:bg-white/10"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </DialogHeader>

          {/* Search Bar */}
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/60" />
            <Input
              type="text"
              placeholder="Search for your job title (e.g., Data Scientist, Frontend Developer, DevOps Engineer)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full py-4 pl-12 pr-6 text-lg bg-white/10 border-white/20 text-white placeholder:text-white/60 backdrop-blur-sm rounded-xl"
            />
          </div>

          {/* Job Categories */}
          <div className="space-y-6">
            {filteredJobs.map((category, categoryIndex) => (
              <div key={categoryIndex} className="space-y-3">
                <div className="flex items-center gap-3">
                  <category.icon className="w-5 h-5 text-amber-400" />
                  <h3 className="text-lg font-semibold text-white">{category.title}</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {category.jobs.map((job, jobIndex) => (
                    <Button
                      key={jobIndex}
                      variant="outline"
                      onClick={() => handleJobSelect(job)}
                      className="h-auto py-3 px-4 text-left bg-white/10 border-white/20 text-white hover:bg-white/20 hover:border-white/40 transition-all duration-200 rounded-lg"
                    >
                      {job}
                    </Button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {selectedJobTitle && (
            <div className="mt-6 p-4 bg-white/10 rounded-xl border border-white/20">
              <p className="text-white/90 mb-3">Selected Job Title:</p>
              <Badge variant="secondary" className="bg-amber-600 text-white px-3 py-1 text-sm">
                {selectedJobTitle}
              </Badge>
              <div className="mt-4 space-y-2">
                <p className="text-white/90 text-sm">Select difficulty level:</p>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="bg-green-600/20 border-green-500 text-green-200 hover:bg-green-600/30">
                    Beginner
                  </Button>
                  <Button size="sm" variant="outline" className="bg-yellow-600/20 border-yellow-500 text-yellow-200 hover:bg-yellow-600/30">
                    Intermediate
                  </Button>
                  <Button size="sm" variant="outline" className="bg-red-600/20 border-red-500 text-red-200 hover:bg-red-600/30">
                    Advanced
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EnhancedInterviewQuestions;