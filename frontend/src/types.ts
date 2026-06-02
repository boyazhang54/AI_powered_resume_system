export interface EducationItem {
  school?: string | null;
  degree?: string | null;
  major?: string | null;
  period?: string | null;
}

export interface ProjectItem {
  name?: string | null;
  role?: string | null;
  description?: string | null;
  technologies: string[];
}

export interface ResumeProfile {
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  job_intention?: string | null;
  expected_salary?: string | null;
  years_of_experience?: string | null;
  education: EducationItem[];
  projects: ProjectItem[];
  skills: string[];
}

export interface ResumeParseResult {
  resume_id: string;
  cached: boolean;
  raw_text: string;
  cleaned_text: string;
  profile: ResumeProfile;
}

export interface RadarScore {
  label: string;
  value: number;
}

export interface MatchResult {
  resume_id: string;
  cached: boolean;
  analysis_mode: 'rule_based' | 'ai_enhanced';
  score: number;
  keyword_match_rate: number;
  matched_keywords: string[];
  missing_keywords: string[];
  semantic_matches: RequirementMatch[];
  missing_skill_details: MissingSkillDetail[];
  radar_scores: RadarScore[];
  dimension_scores: Record<string, number>;
  experience_relevance: string;
  ai_summary: string;
}

export interface User {
  id: number;
  username: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HistoryItem {
  id: number;
  resume_id: string;
  candidate_name: string;
  contact: string;
  job_title: string;
  score: number;
  analysis_mode: 'rule_based' | 'ai_enhanced';
  created_at: string;
}

export interface RequirementMatch {
  requirement: string;
  normalized_skill?: string | null;
  matched: boolean;
  match_level: 'strong' | 'partial' | 'weak' | 'none';
  score: number;
  importance: 'high' | 'medium' | 'low';
  evidence?: string | null;
  reason?: string | null;
}

export interface MissingSkillDetail {
  skill: string;
  normalized_skill?: string | null;
  importance: 'high' | 'medium' | 'low';
  reason?: string | null;
}
