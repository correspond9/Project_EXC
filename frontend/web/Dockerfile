FROM nginx:1.27-alpine

# Remove default nginx page
RUN rm -f /usr/share/nginx/html/index.html

# Copy our placeholder page
COPY public/ /usr/share/nginx/html/

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;", "-p", "/etc/nginx", "-c", "/etc/nginx/nginx.conf"]
