from torch.optim.optimizer import Optimizer, required
import copy

class PIDOPT(Optimizer):
    r"""Implements stochastic gradient descent (optionally with momentum).
    Nesterov momentum is based on the formula from
    `On the importance of initialization and momentum in deep learning`__.
    Args:
        params (iterable): iterable of parameters to optimize or dicts defining
            parameter groups
        lr (float): learning rate
        momentum (float, optional): momentum factor (default: 0)
        weight_decay (float, optional): weight decay (L2 penalty) (default: 0)
        dampening (float, optional): dampening for momentum (default: 0)
        nesterov (bool, optional): enables Nesterov momentum (default: False)
    Example:
        >>> optimizer = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
        >>> optimizer.zero_grad()
        >>> loss_fn(model(input), target).backward()
        >>> optimizer.step()
    __ http://www.cs.toronto.edu/%7Ehinton/absps/momentum.pdf
    .. note::
        The implementation of SGD with Momentum/Nesterov subtly differs from
        Sutskever et. al. and implementations in some other frameworks.
        Considering the specific case of Momentum, the update can be written as
        .. math::
                  v = \rho * v + g \\
                  p = p - lr * v
        where p, g, v and :math:`\rho` denote the parameters, gradient,
        velocity, and momentum respectively.
        This is in contrast to Sutskever et. al. and
        other frameworks which employ an update of the form
        .. math::
             v = \rho * v + lr * g \\
             p = p - v
        The Nesterov version is analogously modified.
    """

    def __init__(self, params, lr=required, momentum=0, dampening=0,
                 weight_decay=0, nesterov=False, I=0.9, D=-0.5):
        defaults = dict(lr=lr, momentum=momentum, dampening=dampening,
                        weight_decay=weight_decay, nesterov=nesterov, I=I, D=D)
        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError("Nesterov momentum requires a momentum and zero dampening")
        super(PIDOPT, self).__init__(params, defaults)

    def __setstate__(self, state):
        super(PIDOPT, self).__setstate__(state)
        for group in self.param_groups:
            group.setdefault('nesterov', False)

    def step(self, closure=None):
        """Performs a single optimization step.
        Arguments:
            closure (callable, optional): A closure that reevaluates the model
                and returns the loss.
        """
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            weight_decay = group['weight_decay']
            momentum = group['momentum']
            dampening = group['dampening']
            nesterov = group['nesterov']

            I = group['I']
            D = group['D'] 
            for p in group['params']:
                if p.grad is None:
                    continue
                d_p = p.grad.data
                if weight_decay != 0:
                    d_p.add_(weight_decay, p.data)

                param_state = self.state[p]
                
                if 'grad_buffer' not in param_state:
                    param_state['grad_buffer'] = copy.deepcopy(d_p)

                g_buf = param_state['grad_buffer'] 
                                                               
                if 'I_buffer' not in param_state:
                    I_buf = param_state['I_buffer'] = copy.deepcopy(p.data)
                    
                I_buf = param_state['I_buffer']
                I_buf.mul_(momentum).add_(group['lr'], d_p)

                if 'D_buffer' not in param_state:
                    D_buf = param_state['D_buffer'] = copy.deepcopy(p.grad.data)

                D_buf = param_state['D_buffer']
                D_buf.mul_(momentum).add_(group['lr'], d_p-g_buf)      
                     
                param_state['grad_buffer'] = d_p                            
                p.data.add_(-group['lr'], d_p).add_(-I, I_buf).add_(-D, D_buf)

        return loss
