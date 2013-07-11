require 'rest_client'
require 'json'

class LxcNode
  def initialize(name)
    @name = name
    set_ip()
  end
  def ip
    @ip
  end
  def name
    @name
  end
  def is_created()
    cont = JSON.parse(RestClient.get("http://localhost:8080/containers/#@name"))
    containers['containers'].each do |container|
      if container['name'] == @name
        return True
      end
    end
    return False
  end
  def create(template, args={})
    post_data = {}
    post_data[:name]=@name
    post_data[:template]=template
	post_data[:args]=args
    puts "Creating host node..."
    puts post_data.to_json
    RestClient.post('http://localhost:8080/containers', post_data.to_json, :content_type => :json, :accept => :json )
  end
  def start()
    puts "Starting host node..."
    RestClient.post("http://localhost:8080/containers/#@name/actions/start", '')
    puts "Waiting for sshd"
    set_ip()
    print (".") until tcp_test_ssh() { sleep 10 }
    puts " OK!"
  end
  def set_ip()
    cont = JSON.parse(RestClient.get("http://localhost:8080/containers/#@name/ips"))
    if cont['ips'].kind_of?(Array)
      @ip=cont['ips'][0]
      puts "ip is #@ip"
    end
  end
  def run_ssh(cmd)
    system "ssh #@ip '#{cmd}'"
  end 
  def set_user_sshkey(user,key)
    puts "!!!! set_user_sshkey unimplemented :!!!!!"
    return false
  end
  def set_user_passwd(user,password)
    post_data = {}
    post_data[:cmd] = "echo #{user}:#{password} | chpasswd"
    RestClient.post("http://localhost:8080/containers/#@name/actions/chrootexec", post_data.to_json, :content_type => :json, :accept => :json )
  end
  def tcp_test_ssh()
    tcp_socket = TCPSocket.new(@ip, 22)
    readable = IO.select([tcp_socket], nil, nil, 5)
    if readable
      yield
      true
    else
      false
    end
  rescue Errno::ETIMEDOUT
    false
  rescue Errno::EPERM
    false
  rescue Errno::ECONNREFUSED
    sleep 2
    false
  rescue Errno::EHOSTUNREACH
    sleep 2
    false
  ensure
    tcp_socket && tcp_socket.close
  end
end

module KnifeLxc
  LXC_CONFIG_PATHS = ['/tmp', '/etc/lxc']

  class LxcServerList < Chef::Knife

    banner "knife lxc server list"

    # This method will be executed when you run this knife command.
    def run
      puts "Lxc containers list"
      require 'restclient'
      containers = JSON.parse(RestClient.get('http://localhost:8080/containers'))
      server_list = [
        ui.color('Name', :bold),
          ui.color('Ip', :bold),
       ui.color('State', :bold),
      ]
      containers['containers'].each do |container|
        node = LxcNode.new(container['name'])
        server_list << container['name']
        server_list << node.ip
        server_list << container['state']
      end
      puts ui.list(server_list, :uneven_columns_across, 3)
    end
  end
  
  class LxcServerCreate < Chef::Knife
    deps do
      require 'chef/knife/bootstrap'
      Chef::Knife::Bootstrap.load_deps
    end
    banner "knife lxc server create -N NAME (options)"
    

    option :node_name,
      :short => "-N NAME",
      :long => "--node-name NAME",
      :description => "Container name and chef node name",
      :required => true

    option :node_ip,
      :long => "--ip IP",
      :description => "Ip for new container",
      :default => "192.168.20.#{(rand(222 - 100) +100)}"

    option :lxc_template,
      :short => "-t NAME",
      :long => "--lxc-template NAME",
      :description => "lxc template user for container",
      :required => true

	option :lxc_template_args,
      :short => "-l JSON",
      :long => "--lxc-template JSON",
      :description => "lxc template user for container",
      :required => false

    option :distro,
      :short => "-d DISTRO",
      :long => "--distro DISTRO",
      :description => "Bootstrap a lxc container using a template; default is 'lucid-chef'",
      :default => "chef-full"

    option :run_list,
      :short => "-r RUN_LIST",
      :long => "--run-list RUN_LIST",
      :description => "Comma separated list of roles/recipes to apply",
      :proc => lambda { |o| o.split(/[\s,]+/) },
      :default => []    

    option :ssh_user,
      :short => "-x USERNAME",
      :long => "--ssh-user USERNAME",
      :description => "The ssh username",
      :default => "root"

    option :ssh_password,
      :short => "-P PASSWORD",
      :long => "--ssh-password PASSWORD",
      :description => "The ssh password"

    option :identity_file,
      :short => "-i IDENTITY_FILE",
      :long => "--identity-file IDENTITY_FILE",
      :description => "The SSH identity file used for authentication (user for bootstrap)"

    option :ssh_pubkey,
      :short => "-i PUBKEY_FILE",
      :long => "--ssh-pubkey PUBKEY_FILE",
      :description => "The SSH public key to push in user (see ssh_user option) authorized_keys"

    # This method will be executed when you run this knife command.
    def run
      puts "Creating lxc container '#{config[:node_name]}' with ip '#{config[:node_ip]}' from template '#{config[:distro]}'"
	  node = LxcNode.new(config[:node_name])
	  if config.has_key?(:lxc_template_args)
		  node.create(config[:lxc_template], config[:lxc_template_args])
	  else
		  node.create(config[:lxc_template])
	  end
      puts "configuring conatiner auth"
      if config.has_key?(:ssh_password)
        node.set_user_passwd(config[:ssh_user],config[:ssh_password])
      elsif
        node.set_user_sshkey(config[:ssh_user],config[:identity_file])
      else
        puts "No passwd or ssh_key setuped for user #{config[:ssh_user]}, let's hope you don't need it..."
      end
      puts "Starting lxc container '#{config[:node_name]}"
      node.start()
      puts "Run chef client with run list: #{config[:run_list].join(' ')}"
      bootstrap = Chef::Knife::Bootstrap.new
      bootstrap.name_args = [node.ip]
      bootstrap.config[:run_list] = config[:run_list]
      bootstrap.config[:ssh_user] = config[:ssh_user]
      bootstrap.config[:identity_file] = config[:identity_file]
      bootstrap.config[:ssh_password] = config[:ssh_password]
      bootstrap.config[:distro] = config[:distro]
      bootstrap.config[:no_host_key_verify] = true
      bootstrap.config[:use_sudo] = true unless config[:ssh_user] == 'root'
      bootstrap.run
      puts "Node created! Details: ip => #{node.ip}, name => #{node.name} "
    end

    private
    def run_chef(node, run_list, environment)
      set_run_list node.name, run_list
      env_string = environment.nil? ? "" : "-E #{environment}"
      node.run_ssh("chef-client -j /etc/chef/first-boot.json #{env_string}")
    end

  end
end
