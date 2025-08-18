import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { AlertCircle, Clock, CheckCircle, X, ArrowLeft, RotateCcw } from 'lucide-react';
import { fetchLogicalQuestions } from '../services/api';
import { useToast } from '../hooks/use-toast';

const QuestionPracticeSession = ({ 
  category, 
  difficulty, 
  onBack, 
  maxQuestions = 10 
}) => {
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [answers, setAnswers] = useState({});
  const [showResult, setShowResult] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { toast } = useToast();

  // Timer effect
  useEffect(() => {
    if (!isLoading && !showResult) {
      const timer = setInterval(() => {
        setTimeSpent(prev => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [isLoading, showResult]);

  // Fetch questions from API
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        console.log(`Fetching ${category} questions with difficulty ${difficulty}`);
        
        // Map difficulty levels to API values
        const difficultyMap = {
          'foundation': 'foundation',
          'placement-ready': 'placement_ready', 
          'campus-expert': 'campus_expert'
        };
        
        const apiDifficulty = difficultyMap[difficulty] || difficulty;
        
        let questionData;
        
        if (category === 'logical') {
          questionData = await fetchLogicalQuestions(maxQuestions, apiDifficulty);
        } else {
          // For other categories, use generic fetch
          const { fetchQuestionsByCategory } = await import('../services/api');
          questionData = await fetchQuestionsByCategory(category, maxQuestions);
        }
        
        console.log('Questions response:', questionData);
        
        if (questionData && questionData.questions && questionData.questions.length > 0) {
          setQuestions(questionData.questions);
          toast({
            title: "Questions Loaded Successfully!",
            description: `Loaded ${questionData.questions.length} ${category} questions`
          });
        } else {
          throw new Error('No questions found for this category');
        }
      } catch (error) {
        console.error('Error loading questions:', error);
        setError(error.message);
        toast({
          title: "Error Loading Questions",
          description: error.message,
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadQuestions();
  }, [category, difficulty, maxQuestions, toast]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const currentQuestion = questions[currentQuestionIndex];

  const handleAnswerSelect = (option) => {
    setSelectedAnswer(option);
  };

  const handleNextQuestion = () => {
    if (selectedAnswer) {
      setAnswers(prev => ({
        ...prev,
        [currentQuestionIndex]: selectedAnswer
      }));
      
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setSelectedAnswer('');
      } else {
        setShowResult(true);
      }
    } else {
      toast({
        title: "Please select an answer",
        description: "You must select an answer before proceeding."
      });
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setSelectedAnswer(answers[currentQuestionIndex - 1] || '');
    }
  };

  const calculateResults = () => {
    let correctCount = 0;
    questions.forEach((question, index) => {
      if (answers[index] === question.correct_answer) {
        correctCount++;
      }
    });
    return {
      correct: correctCount,
      total: questions.length,
      percentage: Math.round((correctCount / questions.length) * 100)
    };
  };

  const handleRestart = () => {
    setCurrentQuestionIndex(0);
    setSelectedAnswer('');
    setAnswers({});
    setShowResult(false);
    setTimeSpent(0);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6 flex items-center justify-center">
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle className="text-center">Loading Questions...</CardTitle>
            <CardDescription className="text-center">
              Fetching {category} questions with {difficulty} difficulty
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Please wait while we load your questions</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6 flex items-center justify-center">
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle className="text-center text-red-600 flex items-center justify-center gap-2">
              <AlertCircle className="w-6 h-6" />
              Error Loading Questions
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-gray-600">{error}</p>
            <div className="flex gap-4 justify-center">
              <Button onClick={onBack} variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Go Back
              </Button>
              <Button onClick={() => window.location.reload()}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (showResult) {
    const results = calculateResults();
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6">
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-2xl">
                🎉 Practice Session Complete!
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Results Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-3xl font-bold text-green-600">{results.correct}</div>
                    <div className="text-sm text-gray-600">Correct Answers</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-3xl font-bold text-blue-600">{results.percentage}%</div>
                    <div className="text-sm text-gray-600">Score</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-6 text-center">
                    <div className="text-3xl font-bold text-purple-600">{formatTime(timeSpent)}</div>
                    <div className="text-sm text-gray-600">Time Taken</div>
                  </CardContent>
                </Card>
              </div>

              {/* Answer Review */}
              <div className="space-y-4">
                <h3 className="text-xl font-semibold">Answer Review</h3>
                {questions.map((question, index) => {
                  const userAnswer = answers[index];
                  const isCorrect = userAnswer === question.correct_answer;
                  
                  return (
                    <Card key={index} className={`border-l-4 ${isCorrect ? 'border-l-green-500' : 'border-l-red-500'}`}>
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          {isCorrect ? (
                            <CheckCircle className="w-5 h-5 text-green-500 mt-1 flex-shrink-0" />
                          ) : (
                            <X className="w-5 h-5 text-red-500 mt-1 flex-shrink-0" />
                          )}
                          <div className="flex-1 space-y-2">
                            <p className="font-medium">Q{index + 1}. {question.question_text}</p>
                            <p className="text-sm text-green-600">
                              <strong>Correct Answer:</strong> {question.correct_answer}
                            </p>
                            {!isCorrect && (
                              <p className="text-sm text-red-600">
                                <strong>Your Answer:</strong> {userAnswer}
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 justify-center">
                <Button onClick={onBack} variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Selection
                </Button>
                <Button onClick={handleRestart}>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Practice Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6 flex items-center justify-center">
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle className="text-center">No Questions Available</CardTitle>
            <CardDescription className="text-center">
              No {category} questions found for {difficulty} difficulty level.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-pink-800 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header with Progress */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button onClick={onBack} variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Badge variant="outline" className="capitalize">
                  {category} - {difficulty}
                </Badge>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span>{formatTime(timeSpent)}</span>
                </div>
                <Badge>
                  {currentQuestionIndex + 1} / {questions.length}
                </Badge>
              </div>
            </div>
            <Progress 
              value={((currentQuestionIndex + 1) / questions.length) * 100} 
              className="w-full"
            />
          </CardHeader>
        </Card>

        {/* Current Question */}
        <Card>
          <CardHeader>
            <CardTitle>
              Question {currentQuestionIndex + 1}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-lg font-medium leading-relaxed">
              {currentQuestion.question_text}
            </p>

            {/* Options */}
            <div className="space-y-3">
              {currentQuestion.options.map((option, index) => (
                <Card 
                  key={index}
                  className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                    selectedAnswer === option 
                      ? 'ring-2 ring-purple-500 bg-purple-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => handleAnswerSelect(option)}
                >
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      selectedAnswer === option 
                        ? 'border-purple-500 bg-purple-500' 
                        : 'border-gray-300'
                    }`}>
                      {selectedAnswer === option && (
                        <div className="w-2 h-2 rounded-full bg-white" />
                      )}
                    </div>
                    <span className="flex-1">{option}</span>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6">
              <Button 
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
                variant="outline"
              >
                Previous
              </Button>
              <Button 
                onClick={handleNextQuestion}
                disabled={!selectedAnswer}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {currentQuestionIndex === questions.length - 1 ? 'Finish' : 'Next'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Question Meta Information */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div className="flex items-center gap-4">
                <span>Difficulty: <Badge variant="outline" className="text-xs">{currentQuestion.difficulty}</Badge></span>
                <span>Source: {currentQuestion.scraped_from || 'GeeksforGeeks'}</span>
              </div>
              <div>
                Quality Score: {currentQuestion.ai_metrics?.quality_score || 85}/100
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default QuestionPracticeSession;