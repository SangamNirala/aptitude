// Mock data for interview questions functionality
export const mockJobCategories = [
  {
    id: 'software-engineering',
    title: 'Software & Engineering',
    jobs: [
      'Frontend Developer',
      'Backend Engineer', 
      'Full Stack Developer',
      'Software Engineer',
      'Mobile App Developer',
      'Game Developer',
      'Embedded Systems Engineer',
      'DevOps Engineer',
      'Site Reliability Engineer (SRE)'
    ]
  },
  {
    id: 'data-ai',
    title: 'Data & AI',
    jobs: [
      'Data Scientist',
      'Data Analyst',
      'Machine Learning Engineer',
      'Data Engineer',
      'AI Researcher',
      'Business Intelligence (BI) Analyst',
      'Statistician'
    ]
  },
  {
    id: 'cloud-infrastructure',
    title: 'Cloud & Infrastructure',
    jobs: [
      'Cloud Engineer',
      'Solutions Architect',
      'Security Engineer',
      'Network Engineer',
      'Cloud DevOps Engineer'
    ]
  },
  {
    id: 'design-ux',
    title: 'Design & UX',
    jobs: [
      'UX Designer',
      'UI Designer',
      'Product Designer',
      'UX Researcher',
      'Interaction Designer'
    ]
  },
  {
    id: 'quality-testing',
    title: 'Quality & Testing',
    jobs: [
      'QA Tester',
      'Automation Test Engineer',
      'Performance Tester',
      'Security Tester',
      'Manual Tester'
    ]
  },
  {
    id: 'product-management',
    title: 'Product & Management',
    jobs: [
      'Product Manager',
      'Technical Product Manager',
      'Project Manager',
      'Scrum Master',
      'Program Manager'
    ]
  }
];

export const mockQuestionTypes = [
  {
    id: 'aptitude',
    title: 'Aptitude Questions',
    description: 'Numerical, Logical, Verbal & Spatial Reasoning',
    color: 'blue',
    available: false
  },
  {
    id: 'technical',
    title: 'Technical Interview Questions',
    description: 'Role-specific technical challenges and problem-solving',
    color: 'orange',
    available: true
  },
  {
    id: 'behavioral',
    title: 'Behavioral Interview Questions',
    description: 'Soft skills, teamwork, and situational responses',
    color: 'teal',
    available: false
  }
];

export const mockQuickTips = [
  'Be specific with job titles (e.g., "React Developer" vs "Developer")',
  'Include seniority level (Junior, Senior, Lead, Principal)',
  'Add domain context (e.g., "Healthcare Data Analyst", "E-commerce Backend Developer")',
  'Specify technologies if relevant (e.g., "Python ML Engineer", "React Native Developer")'
];

// Mock function to simulate search
export const searchJobs = (query, categories = mockJobCategories) => {
  if (!query.trim()) return categories;
  
  return categories.map(category => ({
    ...category,
    jobs: category.jobs.filter(job => 
      job.toLowerCase().includes(query.toLowerCase())
    )
  })).filter(category => category.jobs.length > 0);
};