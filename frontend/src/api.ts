export type ApiError = { detail: string; code?: string; fields?: Record<string, string[]> };
export type SessionUser = { id: string; email: string; first_name: string; last_name: string; preferred_language: 'en' | 'fa' | 'ps' };
export type Session = { access: string; user: SessionUser };
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:58000/api/v1';
let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;
export const setAccessToken = (value: string | null) => { accessToken = value; };
function csrfToken() { return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=').slice(1).join('=') ?? ''; }

async function refreshAccess(): Promise<string | null> {
 if (refreshInFlight) return refreshInFlight;
 refreshInFlight = (async()=>{
  try {
   const response=await fetch(`${API_BASE}/accounts/auth/refresh/`,{method:'POST',credentials:'include',headers:{'X-CSRFToken':decodeURIComponent(csrfToken()),Accept:'application/json'}});
   if(!response.ok){accessToken=null;return null;}
   const data=await response.json() as {access:string};accessToken=data.access;return data.access;
  } catch { accessToken=null;return null; }
  finally { refreshInFlight=null; }
 })();
 return refreshInFlight;
}

export async function apiRequest<T>(path:string,options:RequestInit={},signal?:AbortSignal,retried=false):Promise<T>{
 const headers=new Headers(options.headers);headers.set('Accept','application/json');
 if(options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
 if(accessToken && !headers.has('Authorization')) headers.set('Authorization',`Bearer ${accessToken}`);
 const response=await fetch(`${API_BASE}${path}`,{...options,headers,signal:signal??options.signal,credentials:'include'});
 if(response.status===401 && !retried && !path.includes('/auth/')){const token=await refreshAccess();if(token)return apiRequest<T>(path,options,signal,true);}
 if(response.status===204)return undefined as T;
 const body=await response.json().catch(()=>({}));
 if(!response.ok){const error=body as Partial<ApiError>;throw {detail:error.detail??'The request could not be completed.',code:error.code,fields:error.fields} satisfies ApiError;}
 return body as T;
}

export async function loginRequest(email:string,password:string):Promise<Session>{
 const response=await fetch(`${API_BASE}/accounts/auth/login/`,{method:'POST',credentials:'include',headers:{Accept:'application/json','Content-Type':'application/json'},body:JSON.stringify({email,password})});
 const body=await response.json().catch(()=>({}));
 if(!response.ok)throw {detail:body.detail??'Unable to sign in.',code:body.code,fields:body.fields} satisfies ApiError;
 const session=body as Session;accessToken=session.access;return session;
}
export async function restoreSession():Promise<SessionUser|null>{const access=await refreshAccess();if(!access)return null;try{return await apiRequest<SessionUser>('/accounts/auth/me/');}catch{return null;}}
export async function logoutRequest(){try{await fetch(`${API_BASE}/accounts/auth/logout/`,{method:'POST',credentials:'include',headers:{'X-CSRFToken':decodeURIComponent(csrfToken()),Accept:'application/json'}});}finally{accessToken=null;}}
export type HealthResponse={status:'ok';service:string};
export const getHealth=(signal?:AbortSignal)=>apiRequest<HealthResponse>('/health/',{},signal);

export async function downloadAccountExport():Promise<Blob>{
 let headers=new Headers({Accept:'application/json'});if(accessToken)headers.set('Authorization',`Bearer ${accessToken}`);
 let response=await fetch(`${API_BASE}/accounts/me/export/`,{headers,credentials:'include'});
 if(response.status===401){const token=await refreshAccess();if(token){headers.set('Authorization',`Bearer ${token}`);response=await fetch(`${API_BASE}/accounts/me/export/`,{headers,credentials:'include'});}}
 if(!response.ok)throw new Error('Unable to download account data.');return response.blob();
}

export async function getPrivateImage(path:string):Promise<string>{
 let headers=new Headers();if(accessToken)headers.set('Authorization',`Bearer ${accessToken}`);let response=await fetch(`${API_BASE}${path}`,{headers,credentials:'include'});if(response.status===401){const token=await refreshAccess();if(token){headers.set('Authorization',`Bearer ${token}`);response=await fetch(`${API_BASE}${path}`,{headers,credentials:'include'});}}if(!response.ok)throw new Error('Private image unavailable');return URL.createObjectURL(await response.blob());
}

export type Page<T>={count:number;next:string|null;previous:string|null;results:T[]};
export async function apiList<T>(path:string):Promise<T[]> {
 const items:T[]=[];let page=1;
 while(true){const result=await apiRequest<Page<T>|T[]>(`${path}${path.includes('?')?'&':'?'}page=${page}`);if(Array.isArray(result))return result;items.push(...result.results);if(!result.next)return items;page++;}
}

export async function getPrivateFile(path:string):Promise<Blob>{
 let headers=new Headers();if(accessToken)headers.set('Authorization',`Bearer ${accessToken}`);let response=await fetch(`${API_BASE}${path}`,{headers,credentials:'include'});if(response.status===401){const token=await refreshAccess();if(token){headers.set('Authorization',`Bearer ${token}`);response=await fetch(`${API_BASE}${path}`,{headers,credentials:'include'});}}if(!response.ok)throw new Error('Private file unavailable');return response.blob();
}
