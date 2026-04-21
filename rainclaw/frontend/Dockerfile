# Use nginx as production environment image
FROM crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/nginx:stable-alpine

WORKDIR /app

# Copy built files to nginx
COPY dist /usr/share/nginx/html

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf.template

# Expose port 80
EXPOSE 80

# Start nginx with environment variable substitution
CMD ["/docker-entrypoint.sh"] 
# CMD /docker-entrypoint.sh