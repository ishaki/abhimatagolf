import api from './api';

export interface Teebox {
  id: number;
  course_id: number;
  name: string;
  course_rating: number;
  slope_rating: number;
  created_at: string;
  updated_at: string;
}

export interface TeeboxCreate {
  name: string;
  course_rating: number;
  slope_rating: number;
}

export interface TeeboxUpdate {
  name?: string;
  course_rating?: number;
  slope_rating?: number;
}

export interface Hole {
  id: number;
  course_id: number;
  number: number;
  par: number;
  stroke_index: number;
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
  teeboxes: Teebox[];
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
  stroke_index: number;
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

// Teebox Management Functions

export const getCourseTeeboxes = async (courseId: number): Promise<Teebox[]> => {
  const response = await api.get(`/courses/${courseId}/teeboxes/`);
  return response.data;
};

export const createTeebox = async (courseId: number, teeboxData: TeeboxCreate): Promise<Teebox> => {
  const response = await api.post(`/courses/${courseId}/teeboxes/`, teeboxData);
  return response.data;
};

export const updateTeebox = async (courseId: number, teeboxId: number, teeboxData: TeeboxUpdate): Promise<Teebox> => {
  const response = await api.put(`/courses/${courseId}/teeboxes/${teeboxId}/`, teeboxData);
  return response.data;
};

export const deleteTeebox = async (courseId: number, teeboxId: number): Promise<void> => {
  await api.delete(`/courses/${courseId}/teeboxes/${teeboxId}/`);
};
