import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { 
  Search, BookOpen, Code, Users, Lightbulb, X, Calculator, Brain, 
  FileText, BarChart3, Building2, Trophy, Clock, Target, ChevronRight 
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const InterviewQuestions = () => {
  const [jobTitle, setJobTitle] = useState('');
  const [isTechnicalModalOpen, setIsTechnicalModalOpen] = useState(false);
  const [isAptitudeModalOpen, setIsAptitudeModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJobTitle, setSelectedJobTitle] = useState('');
  const [selectedAptitudeCategory, setSelectedAptitudeCategory] = useState('');
  const [selectedSubtopic, setSelectedSubtopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');

  const { toast } = useToast();

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

  const aptitudeCategories = [
    {
      id: 'quantitative',
      title: 'Quantitative Aptitude',
      icon: Calculator,
      description: 'Mathematical problem-solving skills',
      color: 'bg-blue-600',
      subtopics: [
        'Percentages', 'Profit & Loss', 'Time, Speed & Distance', 'Time & Work',
        'Averages', 'Number Systems', 'Simplification', 'HCF & LCM',
        'Permutations & Combinations', 'Probability'
      ]
    },
    {
      id: 'logical',
      title: 'Logical Reasoning',
      icon: Brain,
      description: 'Critical thinking and pattern recognition',
      color: 'bg-purple-600',
      subtopics: [
        'Blood Relations', 'Direction Sense', 'Syllogisms', 'Puzzles & Seating Arrangement',
        'Coding-Decoding', 'Series & Pattern Recognition', 'Data Sufficiency'
      ]
    },
    {
      id: 'verbal',
      title: 'Verbal Ability',
      icon: FileText,
      description: 'English language proficiency',
      color: 'bg-green-600',
      subtopics: [
        'Reading Comprehension', 'Error Spotting', 'Sentence Improvement',
        'Para Jumbles', 'Fill in the Blanks', 'Synonyms & Antonyms'
      ]
    },
    {
      id: 'data-interpretation',
      title: 'Data Interpretation',
      icon: BarChart3,
      description: 'Analyzing charts, graphs, and data',
      color: 'bg-orange-600',
      subtopics: [
        'Pie Charts', 'Bar Graphs', 'Line Graphs', 'Tables', 'Caselets'
      ]
    }
  ];

  const companies = [
    { name: 'TCS NQT', logo: Building2 },
    { name: 'Infosys', logo: Building2 },
    { name: 'Wipro Elite', logo: Building2 },
    { name: 'Cognizant GenC', logo: Building2 },
    { name: 'Accenture', logo: Building2 },
    { name: 'Capgemini', logo: Building2 },
    { name: 'Tech Mahindra', logo: Building2 },
    { name: 'HCL', logo: Building2 }
  ];

  const difficultyLevels = [
    { id: 'beginner', name: 'Beginner', color: 'bg-green-600', description: 'Foundation level' },
    { id: 'intermediate', name: 'Intermediate', color: 'bg-yellow-600', description: 'Moderate complexity' },
    { id: 'advanced', name: 'Advanced', color: 'bg-red-600', description: 'Expert level' }
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

  const handleStartPractice = () => {
    if (!selectedAptitudeCategory || !selectedDifficulty) {
      toast({
        title: "Selection Required",
        description: "Please select a category and difficulty level to start practice."
      });
      return;
    }
    toast({
      title: "Starting Practice!",
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
              <div>
                <h3 className="text-xl font-semibold">Aptitude Questions</h3>
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

      {/* Modal for Technical Interview Questions */}
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

      {/* Modal for Aptitude Questions - Placement Preparation */}
      <Dialog open={isAptitudeModalOpen} onOpenChange={setIsAptitudeModalOpen}>
        <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto bg-gradient-to-br from-indigo-900 via-blue-900 to-cyan-900 border-blue-700/50 text-white [&>button]:hidden">
          <DialogHeader className="pb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Target className="w-7 h-7 text-cyan-400" />
                <DialogTitle className="text-3xl font-bold text-white">Aptitude Questions – Placement Preparation</DialogTitle>
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
            <p className="text-blue-200 text-lg mt-2">Choose an Aptitude Category for Your Tech Placement Preparation</p>
          </DialogHeader>

          <Tabs defaultValue="categories" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 bg-white/10 border border-white/20">
              <TabsTrigger value="categories" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                Practice by Category
              </TabsTrigger>
              <TabsTrigger value="companies" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
                Company-Specific
              </TabsTrigger>
            </TabsList>

            <TabsContent value="categories" className="space-y-6">
              {/* Main Aptitude Categories */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {aptitudeCategories.map((category) => (
                  <Card 
                    key={category.id} 
                    className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                      selectedAptitudeCategory === category.id 
                        ? 'border-cyan-400 bg-white/20' 
                        : 'border-white/20 bg-white/10'
                    } hover:bg-white/20`}
                    onClick={() => handleAptitudeCategorySelect(category)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-lg ${category.color}`}>
                          <category.icon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <CardTitle className="text-white text-xl">{category.title}</CardTitle>
                          <CardDescription className="text-blue-200 mt-1">
                            {category.description}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {category.subtopics.slice(0, 4).map((subtopic, index) => (
                          <Badge 
                            key={index} 
                            variant="secondary" 
                            className="bg-white/20 text-white text-xs px-2 py-1"
                          >
                            {subtopic}
                          </Badge>
                        ))}
                        {category.subtopics.length > 4 && (
                          <Badge variant="secondary" className="bg-white/20 text-white text-xs px-2 py-1">
                            +{category.subtopics.length - 4} more
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Subtopics Selection */}
              {selectedAptitudeCategory && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-cyan-400" />
                    Choose Specific Topics (Optional)
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {aptitudeCategories
                      .find(cat => cat.id === selectedAptitudeCategory)
                      ?.subtopics.map((subtopic, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          onClick={() => handleSubtopicSelect(subtopic)}
                          className={`h-auto py-2 px-3 text-left justify-start ${
                            selectedSubtopic === subtopic
                              ? 'bg-cyan-600 border-cyan-400 text-white'
                              : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                          }`}
                        >
                          {subtopic}
                        </Button>
                      ))}
                  </div>
                </div>
              )}

              {/* Difficulty Level Selection */}
              {selectedAptitudeCategory && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    <Trophy className="w-5 h-5 text-cyan-400" />
                    Select Difficulty Level
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {difficultyLevels.map((difficulty) => (
                      <Card
                        key={difficulty.id}
                        className={`cursor-pointer transition-all duration-300 hover:scale-105 border-2 ${
                          selectedDifficulty === difficulty.id
                            ? 'border-cyan-400 bg-white/20'
                            : 'border-white/20 bg-white/10'
                        } hover:bg-white/20`}
                        onClick={() => handleDifficultySelect(difficulty)}
                      >
                        <CardContent className="p-4 text-center">
                          <div className={`w-12 h-12 mx-auto mb-3 rounded-full ${difficulty.color} flex items-center justify-center`}>
                            <Trophy className="w-6 h-6 text-white" />
                          </div>
                          <h4 className="text-white font-semibold text-lg">{difficulty.name}</h4>
                          <p className="text-blue-200 text-sm mt-1">{difficulty.description}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* Start Practice Button */}
              {selectedAptitudeCategory && selectedDifficulty && (
                <div className="flex justify-center pt-4">
                  <Button 
                    onClick={handleStartPractice}
                    className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white px-8 py-3 text-lg font-semibold rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105"
                  >
                    <Clock className="w-5 h-5 mr-2" />
                    Start Practice Session
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="companies" className="space-y-6">
              <h3 className="text-2xl font-semibold text-white text-center mb-6">
                Company-Specific Placement Practice
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {companies.map((company, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer transition-all duration-300 hover:scale-105 border-2 border-white/20 bg-white/10 hover:bg-white/20 hover:border-cyan-400"
                  >
                    <CardContent className="p-4 text-center">
                      <company.logo className="w-8 h-8 mx-auto mb-3 text-cyan-400" />
                      <h4 className="text-white font-semibold">{company.name}</h4>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              {/* Mock Test Options */}
              <div className="bg-white/10 rounded-xl p-6 border border-white/20">
                <h4 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-cyan-400" />
                  Practice Modes
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Target className="w-6 h-6 text-cyan-400" />
                    <span>Topic-wise Practice</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Clock className="w-6 h-6 text-green-400" />
                    <span>Mock Test Mode</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-yellow-400" />
                    <span>Progress Tracker</span>
                  </Button>
                  <Button variant="outline" className="h-auto py-4 px-4 bg-white/10 border-white/20 text-white hover:bg-white/20 flex flex-col items-center gap-2">
                    <Trophy className="w-6 h-6 text-purple-400" />
                    <span>Daily Challenge</span>
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InterviewQuestions;