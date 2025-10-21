import api from './api';

export interface Hole {
  id: number;
  course_id: number;
  number: number;
  par: number;
  handicap_index: number;
  distance_meters?: number;
  created_at: string;
}

export interface Course {
  id: number;
  name: string;
  location?: string;
  total_holes: number;
  created_at: string;
  updated_at: string;
  holes: Hole[];
}

export interface CourseCreate {
  name: string;
  location?: string;
  total_holes: number;
  holes?: HoleCreate[];
}

export interface CourseUpdate {
  name?: string;
  location?: string;
  total_holes?: number;
}

export interface HoleCreate {
  number: number;
  par: number;
  handicap_index: number;
  distance_meters?: number;
}

export interface CourseListResponse {
  courses: Course[];
  total: number;
  page: number;
  per_page: number;
}

export const getCourses = async (page: number = 1, per_page: number = 20, search?: string): Promise<CourseListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: per_page.toString(),
  });

  if (search) {
    params.append('search', search);
  }

  const response = await api.get(`/courses/?${params.toString()}`);
  return response.data;
};

export const getCourse = async (id: number): Promise<Course> => {
  const response = await api.get(`/courses/${id}/`);
  return response.data;
};

export const createCourse = async (courseData: CourseCreate): Promise<Course> => {
  const response = await api.post('/courses/', courseData);
  return response.data;
};

export const updateCourse = async (id: number, courseData: CourseUpdate): Promise<Course> => {
  const response = await api.put(`/courses/${id}/`, courseData);
  return response.data;
};

export const deleteCourse = async (id: number): Promise<void> => {
  await api.delete(`/courses/${id}/`);
};

export const getCourseHoles = async (courseId: number): Promise<Hole[]> => {
  const response = await api.get(`/courses/${courseId}/holes/`);
  return response.data;
};

export const updateCourseHoles = async (courseId: number, holes: HoleCreate[]): Promise<Hole[]> => {
  const response = await api.post(`/courses/${courseId}/holes/`, holes);
  return response.data;
};
