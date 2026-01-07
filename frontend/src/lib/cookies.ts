 export function getCookie(cookieName: string): string | null {
  let name = cookieName + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
} 

export function setCookie(cookieName: string, cookieValue: string, daysToExpire: number) {
  const expirationDate = new Date();
  expirationDate.setTime(expirationDate.getTime() + (daysToExpire*24*60*60*1000));
  let expires = "expires="+ expirationDate.toUTCString();
  document.cookie = cookieName + "=" + cookieValue + ";" + expires + ";path=/";
}
