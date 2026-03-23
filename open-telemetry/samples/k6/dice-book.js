import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 10,          
  duration: '30s', 
};

export default function () {
  http.get('https://dice.sample:8080/rolldice');
  http.get('http://productpage.sample:9080/productpage?u=normal');
  sleep(1);
}
