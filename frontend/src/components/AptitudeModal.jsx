import React from 'react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { 
  X, Calculator, Brain, FileText, BarChart3, Building2, Trophy, Clock, Target, 
  ChevronRight, TrendingUp, Flame, Star, Zap, Users2, MessageCircle, Award,
  Timer, BookMarked, PlayCircle, RotateCcw, Gamepad2, GraduationCap,
  PieChart, LineChart, Calendar, Bell, Sparkles, Code
} from 'lucide-react';

const AptitudeModal = ({
  isOpen,
  onClose,
  selectedAptitudeCategory,
  selectedSubtopic,
  selectedDifficulty,
  selectedLearningPath,
  selectedStudyMode,
  handleAptitudeCategorySelect,
  handleSubtopicSelect,
  handleDifficultySelect,
  handleLearningPathSelect,
  handleStudyModeSelect,
  handleStartPractice,
  aptitudeCategories,
  smartLevels,
  learningPaths,
  studyModes,
  companies,
  companyPatterns,
  timeManagementTips,
  getTopicPriority
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto bg-gradient-to-br from-indigo-900 via-blue-900 to-cyan-900 border-blue-700/50 text-white [&>button]:hidden">
        <DialogHeader className="pb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-7 h-7 text-cyan-400" />
              <DialogTitle className="text-3xl font-bold text-white">
                Aptitude Questions – Placement Preparation
              </DialogTitle>
              <Badge className="bg-red-500 text-white animate-pulse">
                <Flame className="w-3 h-3 mr-1" />
                WORLD-CLASS
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="text-white hover:bg-white/10"
            >
              <X className="w-6 h-6" />
            </Button>
          </div>
          <p className="text-blue-200 text-lg mt-2">
            🎯 Choose an Aptitude Category for Your Tech Placement Preparation
          </p>
        </DialogHeader>

        <Tabs defaultValue="categories" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 border border-white/20">
            <TabsTrigger value="categories" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
              Practice by Category
            </TabsTrigger>
            <TabsTrigger value="companies" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
              Company-Specific
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
              Performance Analytics
            </TabsTrigger>
            <TabsTrigger value="paths" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white">
              Learning Paths
            </TabsTrigger>
          </TabsList>

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

            {/* Main Aptitude Categories with Enhanced Features */}
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
                        
                        {/* Success Rate and Average Score */}
                        <div className="flex gap-4 mt-2 text-sm">
                          <span className="text-green-300">
                            📈 Success: {category.successRate}
                          </span>
                          <span className="text-blue-300">
                            📊 Avg Score: {category.avgScore}
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
                    
                    {/* Progress Bar */}
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
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Enhanced Start Practice Button */}
            {selectedAptitudeCategory && selectedDifficulty && (
              <div className="flex justify-center pt-4">
                <Button 
                  onClick={handleStartPractice}
                  className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white px-8 py-4 text-lg font-semibold rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105"
                >
                  <PlayCircle className="w-6 h-6 mr-3" />
                  Start Smart Practice Session
                  <Sparkles className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </TabsContent>

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
                  className="cursor-pointer transition-all duration-300 hover:scale-105 border-2 border-white/20 bg-white/10 hover:bg-white/20 hover:border-cyan-400"
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
          </TabsContent>

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
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default AptitudeModal;